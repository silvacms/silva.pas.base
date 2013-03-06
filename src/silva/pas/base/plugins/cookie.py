# -*- coding: utf-8 -*-
# Copyright (c) 2008-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import time
import urlparse

from zope.interface import implements
from zope.component import getUtility, queryUtility
from zope.component import queryMultiAdapter
from zope.datetime import rfc1123_date
from zope.interface import alsoProvides
from zope.session.interfaces import IClientId
from zope.traversing.browser import absoluteURL

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.PluggableAuthService.PluggableAuthService import \
    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces import plugins
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from silva.pas.base.plugins.interfaces import ICookiePlugin
from silva.pas.base.utils import encode_query

from infrae.wsgi.interfaces import IRequest
from infrae.wsgi.interfaces import IVirtualHosting

from silva.core.cache.store import SessionStore
from silva.core.interfaces import ISilvaObject
from silva.core.layout.interfaces import ISkinLookup
from silva.core.layout.traverser import applySkinButKeepSome
from silva.core.services.interfaces import ISecretService
from silva.core.views.interfaces import IVirtualSite, INonCachedLayer
from silva.translations import translate as _


class SilvaCookieAuthHelper(BasePlugin):
    meta_type = 'Silva Cookie Auth Helper'
    security = ClassSecurityInfo()
    implements(ICookiePlugin)

    # Customize configuration
    cookie_name = '__ac_silva'
    cookie_secure = False
    login_path = 'silva_login_form.html'
    lifetime = 12 * 3600
    include_session_token = True
    redirect_to_path = False
    redirect_to_url = ''
    _properties = (
        {'id': 'title',
         'label': 'Title',
         'type': 'string',
         'mode': 'w'},
        {'id': 'cookie_name',
         'label': 'Cookie Name',
         'type': 'string',
         'mode': 'w'},
        {'id': 'cookie_secure',
         'label': 'Enable secure flag on the cookie',
         'type': 'boolean',
         'mode': 'w'},
        {'id': 'include_session_token',
         'label': 'Include a session token to prevent replay attack',
         'type': 'boolean',
         'mode': 'w'},
        {'id': 'login_path',
         'label': 'Login Form',
         'type': 'string',
         'mode': 'w'},
        {'id': 'lifetime',
         'label': 'Life time (sec)',
         'type': 'int',
         'mode': 'w'},
        {'id': 'redirect_to_path',
         'label': 'Redirect to path instead of URL',
         'type': 'boolean',
         'mode': 'w'},
        {'id': 'redirect_to_url',
         'label': 'Redirect to a different base URL',
         'type': 'string',
         'mode': 'w'})

    def __init__(self, id, title=None, cookie_name=''):
        self._setId(id)
        self.title = title
        if cookie_name:
            self.cookie_name = cookie_name

    def _restore_public_skin(self, request, root):
        lookup = ISkinLookup(root.get_publication(), None)
        if lookup is not None:
            skin = lookup.get_skin(request)
            if skin is not None:
                # We found a skin to apply
                applySkinButKeepSome(request, skin)
        alsoProvides(request, INonCachedLayer)

    def _get_login_page(self, request):
        parent = request.PARENTS and request.PARENTS[0] or None
        if ISilvaObject.providedBy(parent):
            root = parent.get_publication()
        else:
            root = IVirtualSite(request).get_root()
        if request.environ.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            login_path = 'xml_login_form.html'
        else:
            login_path = self.login_path
            # Restory the public skin
            self._restore_public_skin(request, root)

        page = None
        if parent is not None:
            page = queryMultiAdapter((parent, request), name=login_path)
        if page is None:
            page = queryMultiAdapter((root, request), name=login_path)
        if page is not None:
            # Set parent and name for URL (and security)
            page.__parent__ = root
            page.__name__ = '@@' + login_path
        return page

    def _get_session(self, request):
        return SessionStore(request, region='auth')

    def _get_cookie_path(self, request):
        return IVirtualSite(request).get_top_level_path()

    def unauthorized(self, request, response, message=None):
        service = queryUtility(ISecretService)
        if service is None:
            return False

        rewrite_url = None
        if IRequest.providedBy(request):
            vhm_plugin = request.get_plugin(IVirtualHosting)
            if vhm_plugin is not None:
                rewrite_url = vhm_plugin.rewrite_url

        # 1. find the currently unauthorized URL.
        came_from = request.get('__ac.field.origin', None)
        if came_from is None:
            came_from = request.get('ACTUAL_URL', '')
            query = request.form.copy()
            if query:
                for bad in ['login_status', '-C']:
                    if bad in query:
                        del query[bad]
            if query:
                came_from += encode_query(query)

        # 2. do the optional redirect to the wanted backend.
        if self.redirect_to_url:
            if (not came_from.startswith(self.redirect_to_url) and
                rewrite_url is not None):
                response.redirect(rewrite_url(self.redirect_to_url, came_from))
                return True

        # 3. Cleanup, if we already have a auth cookie, delete it.
        if response.cookies.has_key(self.cookie_name):
            del response.cookies[self.cookie_name]

        # 4. Get the login page.
        page = self._get_login_page(request)
        if page is None:
            return False

        options = {}
        if self.include_session_token:
            secret = service.digest(str(IClientId(request)), came_from)
            session = self._get_session(request)
            session.set('secret', secret)
            options['__ac.field.secret'] = secret

        if self.redirect_to_path and rewrite_url is not None:
            # Only include the path
            options['__ac.field.origin'] = rewrite_url(None, came_from)
        else:
            options['__ac.field.origin'] = came_from

        # Set options. The page should not accept to render if action
        # is not set.
        page.message = message
        page.action = absoluteURL(self, request) + '/login'
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
        request = self.REQUEST
        cookie = credentials.get('remote_cookie')
        if cookie is None:
            return None
        service = queryUtility(ISecretService)
        if service is None:
            return None
        session = self._get_session(request)
        user = session.get('user', None)
        login = session.get('login', user)
        timestamp = session.get('timestamp', 0)
        if user is not None and login is not None:
            expected = service.digest(
                str(IClientId(request)),
                login,
                (int(time.time()) - timestamp) / self.lifetime)
            if cookie == expected:
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

        return credentials

    security.declarePrivate('updateCookieCredentials')
    def updateCookieCredentials(self, request, response, user, login):
        """Respond to change of credentials (NOOP for basic auth).
        """
        now = int(time.time())
        timestamp = now % self.lifetime

        session = self._get_session(request)
        session.set('login', login)
        session.set('user', user)
        session.set('timestamp', timestamp)

        service = getUtility(ISecretService)
        cookie = service.digest(
            str(IClientId(request)),
            login,
            (now - timestamp) / self.lifetime)
        response.setCookie(
            self.cookie_name, cookie,
            path=self._get_cookie_path(request),
            expires=rfc1123_date(now + self.lifetime),
            http_only=True,
            secure=self.cookie_secure)

    security.declarePrivate('resetCredentials')
    def resetCredentials(self, request, response):
        """ Raise unauthorized to tell browser to clear credentials.
        """
        path = self._get_cookie_path(request)
        response.expireCookie(self.cookie_name, path=path)
        session = self._get_session(request)
        session.set('login', None)
        session.set('user', None)
        session.set('timestamp', 0)

    security.declarePublic('login')
    def login(self):
        """ Set a cookie and redirect to the url that we tried to
        authenticate against originally.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        login = request.form.get('__ac.field.name', '')
        password = request.form.get('__ac.field.password', '')
        authenticated = False

        if (not login) or (not password):
            self.unauthorized(
                request=request,
                response=response,
                message=_(u"You need to provide a login and a password."))
            return
        else:
            if self.include_session_token:
                secret = request.form.get('__ac.field.secret', '')
                stored_secret = self._get_session(request).get('secret', None)
                if (stored_secret != secret) or request.method != 'POST':
                    self.unauthorized(
                        request = request,
                        response=response,
                        message=_(u"Invalid login or password."))
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
                url = IVirtualSite(request).get_root_url()
                origin = request.form.get('__ac.field.origin')
                if origin is not None:
                    if self.redirect_to_path:
                        url = urlparse.urlunparse(
                            urlparse.urlparse(url)[:2] +
                            urlparse.urlparse(origin)[2:])
                    else:
                        url = origin
                return response.redirect(url)
            self.unauthorized(
                request=request,
                response=response,
                message=_(u"Invalid login or password."))
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
