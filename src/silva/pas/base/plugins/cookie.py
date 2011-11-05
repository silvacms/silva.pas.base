# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from urllib import urlencode
import time
import hashlib

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.PluggableAuthService.PluggableAuthService import \
    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces import plugins
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from silva.pas.base.plugins.interfaces import ICookiePlugin

from silva.core.cache.store import SessionStore
from silva.core.interfaces import ISilvaObject
from silva.core.layout.interfaces import IMetadata
from silva.core.layout.traverser import applySkinButKeepSome
from silva.core.services.interfaces import ISecretService
from silva.core.views.interfaces import IVirtualSite, INonCachedLayer
from zope.interface import implements
from zope import component
from zope.datetime import rfc1123_date
from zope.interface import alsoProvides
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.session.interfaces import IClientId


def encode_query(query):

    def encode_value(value):
        if isinstance(value, list):
            return map(encode_value, value)
        if isinstance(value, basestring):
            return [value.encode('ascii', 'xmlcharrefreplace')]
        # Discard value of other type (FileUpload ...)
        return []

    for key, value in query.items():
        for value in encode_value(value):
            yield key, value


class SilvaCookieAuthHelper(BasePlugin):
    meta_type = 'Silva Cookie Auth Helper'
    security = ClassSecurityInfo()
    implements(ICookiePlugin)

    # Customize configuration
    cookie_name = '__ac_silva'
    login_path = 'silva_login_form.html'
    lifetime = 12 * 3600
    _properties = ({'id'    : 'title',
                    'label' : 'Title',
                    'type'  : 'string',
                    'mode'  : 'w'},
                   {'id'    : 'cookie_name',
                    'label' : 'Cookie Name',
                    'type'  : 'string',
                    'mode'  : 'w'},
                   {'id'    : 'login_path',
                    'label' : 'Login Form',
                    'type'  : 'string',
                    'mode'  : 'w'},
                   {'id'    : 'lifetime',
                    'label' : 'Life time (sec)',
                    'type'  : 'int',
                    'mode'  : 'w'},)

    def __init__(self, id, title=None, cookie_name=''):
        self._setId(id)
        self.title = title
        if cookie_name:
            self.cookie_name = cookie_name

    def _restore_public_skin(self, request, root):
        # Restore public skin site
        metadata = IMetadata(root)
        try:
            name = metadata('silva-layout', 'skin')
            skin = component.queryUtility(IBrowserSkinType, name=name)
            applySkinButKeepSome(request, skin)
        except AttributeError:
            pass
        alsoProvides(request, INonCachedLayer)

    def _get_login_page(self, request):
        parent = request.PARENTS and request.PARENTS[0]
        if ISilvaObject.providedBy(parent):
            root = parent.get_publication()
        else:
            root = IVirtualSite(request).get_root()

        # Restory the public skin
        self._restore_public_skin(request, root)

        page = component.queryMultiAdapter(
            (parent, request), name=self.login_path)
        if page is None:
            # No login page found here, try on the 'root'
            parent = root
            page = component.queryMultiAdapter(
                (parent, request), name=self.login_path)
        if page is not None:
            # Set parent for security check
            page.__parent__ = parent
            page.__name__ = self.login_path
        return page

    def _get_session(self, request):
        return SessionStore(request, region='auth')

    def _get_cookie_path(self, request):
        return IVirtualSite(request).get_root().absolute_url_path()

    def unauthorized(self, request, response, login_status=None):
        service = component.queryUtility(ISecretService)
        if service is None:
            return False

        # If we set the auth cookie before, delete it now.
        if response.cookies.has_key(self.cookie_name):
            del response.cookies[self.cookie_name]
        # Get the login page.
        page = self._get_login_page(request)
        if page is None:
            return False
        came_from = request.get('__ac.field.origin', None)

        if came_from is None:
            came_from = request.get('URL', '')
            query = request.form.copy()
            if query:
                for bad in ['login_status', '-C']:
                    if bad in query:
                        del query[bad]
            if query:
                came_from += '?' + urlencode(list(encode_query(query)))

        secret = service.digest(IClientId(request), came_from)
        session = self._get_session(request)
        session.set('secret', secret)

        options = {}
        options['__ac.field.secret'] = secret
        options['__ac.field.origin'] = came_from
        options['action'] = self.absolute_url() + '/login'
        if login_status is None:
            login_status = request.form.get('login_status', None)
        if login_status is not None:
            options['login_status'] = login_status

        # XXX Need to make sure you can't render the view without
        # passing through that code before as its that code who set
        # the form action
        request.form = options
        # It is not very nice but we don't have lot of choice.
        response.setStatus(401)
        response.write(page())
        return True

    security.declarePrivate('challenge')
    def challenge(self, request, response, **kw):
        """ Challenge the user for credentials. """
        if request is None:
            request = self.REQUEST
        user_agent = request.get('HTTP_USER_AGENT')
        if user_agent and user_agent.startswith('Python-urllib/'):
            # We don't want to redirect to a login form if you are
            # playing with urllib.
            return False
        if response is None:
            response = request['RESPONSE']
        return self.unauthorized(request, response)

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        cookie = credentials.get('remote_cookie')
        address = credentials.get('remote_address')
        if cookie is None or address is None:
            return None
        secret_service = component.queryUtility(ISecretService)
        if secret_service is None:
            return None
        client_secret = secret_service.digest(cookie, address)
        session = self._get_session(self.REQUEST)
        if session.get('secret', None) == client_secret:
            user = session.get('user', None)
            login = session.get('login', user)
            if user is not None:
                return (user, login)
        return None

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract credentials from cookie or 'request'.
        """
        credentials = {}
        cookie = request.get(self.cookie_name, '')
        if cookie and cookie != 'deleted':
            credentials['remote_cookie'] = cookie
            credentials['remote_address'] = request.getClientAddr()

        return credentials

    security.declarePrivate('updateCookieCredentials')
    def updateCookieCredentials(self, request, response, user, login):
        """Respond to change of credentials (NOOP for basic auth).
        """
        service = component.getUtility(ISecretService)
        cookie = hashlib.sha1(str(IClientId(request)) + login).hexdigest()
        secret = service.digest(cookie, request.getClientAddr())
        session = self._get_session(request)
        session.set('secret', secret)
        session.set('login', login)
        session.set('user', user)

        expires = rfc1123_date(time.time() + self.lifetime)
        path = self._get_cookie_path(request)
        response.setCookie(self.cookie_name, cookie, path=path, expires=expires)

    security.declarePrivate('resetCredentials')
    def resetCredentials(self, request, response):
        """ Raise unauthorized to tell browser to clear credentials.
        """
        path = self._get_cookie_path(request)
        response.expireCookie(self.cookie_name, path=path)


    security.declarePublic('login')
    def login(self):
        """ Set a cookie and redirect to the url that we tried to
        authenticate against originally.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        login = request.form.get('__ac.field.name', '')
        password = request.form.get('__ac.field.password', '')
        secret = request.form.get('__ac.field.secret', '')
        authenticated = False

        if (not login) or (not password):
            self.unauthorized(
                request=request,
                response=response,
                login_status=u"You need to provide a login and a password.")
            return
        else:
            stored_secret = self._get_session(request).get('secret', None)
            if (stored_secret != secret) or request.method != 'POST':
                self.unauthorized(
                    request = request,
                    response=response,
                    login_status=u"Invalid login or password")
                return
            credentials = {'login': login, 'password': password,}
            pas = self._getPAS()
            if pas is not None:
                for auth_id, auth in pas.plugins.listPlugins(
                    plugins.IAuthenticationPlugin):
                    try:
                        uid_and_login = auth.authenticateCredentials(
                            credentials)
                        if uid_and_login is None:
                            continue
                        user, login = uid_and_login
                        if user is not None:
                            self.updateCookieCredentials(
                                request, response, user, login)
                            authenticated = True
                            break
                    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                        continue
            if authenticated:
                return response.redirect(request.form['__ac.field.origin'])
            self.unauthorized(
                request=request,
                response=response,
                login_status=u"Invalid login or password")
            return


InitializeClass(SilvaCookieAuthHelper)


manage_addSilvaCookieAuthHelperForm =  PageTemplateFile(
    "../www/cookieAddForm",
    globals(),
    __name__="manage_addSilvaCookieHelperForm")


def manage_addSilvaCookieAuthHelper(
    self, id, title='', REQUEST=None, **kw):
    """Create an instance of an Silva cookie auth helper.
    """
    plugin = SilvaCookieAuthHelper(id, title, **kw)
    self._setObject(plugin.getId(), plugin)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect("%s/manage_workspace"
                "?manage_tabs_message=Silva+cookie+auth+helper+plugin+added." %
                self.absolute_url())
