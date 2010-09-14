# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from urllib import quote, unquote, urlencode
import time

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.PluggableAuthService.PluggableAuthService import \
    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin
from Products.PluggableAuthService.plugins.CookieAuthHelper import \
    CookieAuthHelper

from zope import component
from zope.interface import alsoProvides
from zope.datetime import rfc1123_date
from zope.publisher.interfaces.browser import IBrowserSkinType
from silva.core.layout.traverser import applySkinButKeepSome
from zope.session.interfaces import IClientId
from silva.core.layout.interfaces import IMetadata
from silva.core.views.interfaces import IVirtualSite, INonCachedLayer
from silva.core.cache.store import SessionStore
from silva.core.services.interfaces import ISecretService


def encode_query(query):

    def encode_value(value):
        if isinstance(value, list):
            return map(encode_value, value)
        return [value.encode('ascii', 'xmlcharrefreplace')]

    for key, value in query.items():
        for value in encode_value(value):
            yield key, value


class SilvaCookieAuthHelper(CookieAuthHelper):

    meta_type = 'Silva Cookie Auth Helper'
    security = ClassSecurityInfo()

    # Customize configuration
    cookie_name='__ac_silva'
    login_path = 'silva_login_form.html'
    lifetime = 12 * 3600
    _properties = CookieAuthHelper._properties + (
        {'id'    : 'lifetime',
         'label' : 'Life time (sec)',
         'type'  : 'int',
         'mode'  : 'w'},)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """ Setup tasks upon instantiation
        """
        # This code setup the default login page in ZODB. We don't
        # want to do this.

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
        # Disable caching on the login page.
        root = IVirtualSite(request).get_root()
        self._restore_public_skin(request, root)

        page = component.queryMultiAdapter(
            (root, request), name=self.login_path)
        if page is not None:
            page.__parent__ = root
        return page

    def _get_session(self, request):
        return SessionStore(request, region='auth')

    def unauthorized(self, login_status=None):
        service = component.queryUtility(ISecretService)
        if service is None:
            return 0

        request = self.REQUEST
        response = request['RESPONSE']

        # If we set the auth cookie before, delete it now.
        if response.cookies.has_key(self.cookie_name):
            del response.cookies[self.cookie_name]
        # Get the login page.
        page = self._get_login_page(request)
        if page is None:
            return 0
        came_from = request.get('came_from', None)

        if came_from is None:
            came_from = request.get('URL', '')
            query = request.form.copy()
            if query:
                for bad in ['login_status', '-C']:
                    if bad in query:
                        del query[bad]
            if query:
                came_from += '?' + urlencode(list(encode_query(query)))

        secret = service.create_secret(IClientId(request), came_from)
        session = self._get_session(request)
        session.set('secret', secret)

        options = {}
        options['secret'] = secret
        options['action'] = self.absolute_url() + '/login'
        options['came_from'] = came_from
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
        return 1

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ Extract credentials from cookie or 'request'. """
        credentials = {}
        cookie = request.get(self.cookie_name, '')
        if cookie and cookie != 'deleted':
            session = self._get_session(request)
            if session.get('auth_secret', None) == unquote(cookie):
                login = session.get('login', None)
                password = session.get('password', None)
                if login and password:
                    credentials['login'] = login
                    credentials['password'] = password
        if credentials:
            credentials['remote_host'] = request.get('REMOTE_HOST', '')
            credentials['remote_address'] = request.getClientAddr()

        return credentials

    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, password):
        """Respond to change of credentials (NOOP for basic auth).
        """
        service = component.getUtility(ISecretService)
        secret = service.create_secret(request, login)
        session = self._get_session(request)
        session.set('auth_secret', secret)
        session.set('login', login)
        session.set('password', password)
        expires = rfc1123_date(time.time() + self.lifetime)
        response.setCookie(
            self.cookie_name, quote(secret), path='/', expires=expires)

    security.declarePublic('login')
    def login(self):
        """ Set a cookie and redirect to the url that we tried to
        authenticate against originally.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        login = request.form.get('__ac_name', '')
        password = request.form.get('__ac_password', '')
        secret = request.form.get('__ac_secret', '')
        authenticated = False

        if (not login) or (not password):
            return self.unauthorized(
                login_status=u"You need to provide a login and a password.")
        else:
            stored_secret = self._get_session(request).get('secret', None)
            if (stored_secret != secret) or request.method != 'POST':
                return self.unauthorized(
                    login_status=u"Invalid login or password")
            credentials = {'login': login, 'password': password,}
            pas = self._getPAS()
            if pas is not None:
                for auth_id, auth in pas.plugins.listPlugins(
                    IAuthenticationPlugin):
                    try:
                        uid_and_info = auth.authenticateCredentials(
                            credentials)
                        if uid_and_info is None:
                            continue
                        user_id, info = uid_and_info
                        if user_id is not None:
                            pas.updateCredentials(
                                request, response, login, password)
                            authenticated = True
                            break
                    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                        continue
            if authenticated:
                return response.redirect(request.form['came_from'])
            return self.unauthorized(
                login_status=u"Invalid login or password")


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
