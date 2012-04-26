# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from base64 import encodestring
from urllib import quote
import urlparse
import urllib
import time

from Products.PluggableAuthService.PluggableAuthService import \
    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin
from Products.PluggableAuthService.plugins.CookieAuthHelper import \
    CookieAuthHelper
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Silva import mangle
from Products.Silva.adapters.virtualhosting import VirtualHostingAdapter
from AccessControl.SecurityInfo import ClassSecurityInfo
from Globals import InitializeClass

from zope.datetime import rfc1123_date


def encode_query(query):
    results = []

    def encode_value(key, value):
        if isinstance(value, basestring):
            if isinstance(value, unicode):
                try:
                    value = value.encode('utf-8')
                except UnicodeEncodeError:
                    pass
        elif isinstance(value, (list, tuple)):
            for item in value:
                encode_value(key, item)
            return
        else:
            try:
                value = str(value)
            except:
                pass
        results.append((key, value))

    for key, value in query.items():
        encode_value(key, value)

    if results:
        return '?' + urllib.urlencode(results)
    return ''


def manage_addSilvaCookieAuthHelper(self, id, title='',
                                    REQUEST=None, **kw):
    """Create an instance of an Silva cookie auth helper.
    """

    o = SilvaCookieAuthHelper(id, title, **kw)
    self._setObject(o.getId(), o)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect("%s/manage_workspace"
                "?manage_tabs_message=Silva+cookie+auth+helper+plugin+added." %
                self.absolute_url())



manage_addSilvaCookieAuthHelperForm =  PageTemplateFile("../www/cookieAddForm",
                globals(), __name__="manage_addSilvaCookieHelperForm")


def find_root(context):
    # Find the best looking root in this shitty world.
    root = context.get_root()
    virtual_root = VirtualHostingAdapter(root).getVirtualRoot()
    if virtual_root is None:
        return root
    return virtual_root


class SilvaCookieAuthHelper(CookieAuthHelper):

    meta_type = 'Silva Cookie Auth Helper'
    security = ClassSecurityInfo()

    # Customize configuration
    cookie_name='__ac_silva'
    login_path = 'silva_login_form.html'
    lifetime = 12 * 3600
    redirect_to_path = False
    _properties = CookieAuthHelper._properties + (
        {'id': 'lifetime',
         'label': 'Life time (sec)',
         'type': 'int',
         'mode': 'w'},
        {'id': 'redirect_to_path',
         'label': 'Redirect to path instead of URL',
         'type': 'boolean',
         'mode': 'w'})

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """ Setup tasks upon instantiation """
        pass                    # Do nothing


    def unauthorized(self, login_status=None):
        req = self.REQUEST
        resp = req['RESPONSE']

        # If we set the auth cookie before, delete it now.
        if resp.cookies.has_key(self.cookie_name):
            del resp.cookies[self.cookie_name]

        # Redirect if desired.
        url = self.getLoginURL()
        if url is not None:
            came_from = req.get('came_from', None)

            if came_from is None:
                came_from = req.get('ACTUAL_URL', '')
                query = req.form.copy()
                if query:
                    for bad in ['login_status', '-C']:
                        if bad in query:
                            del query[bad]
                    if query:
                        came_from = encode_query(query)
            else:
                req_url = req.get('ACTUAL_URL', '')

                if req_url and req_url == url:
                    return 0

            options = {}
            if self.redirect_to_path:
                # Only include the path
                options['came_path'] = urlparse.urlunparse(
                    (None, None) + urlparse.urlparse(came_from)[2:])
            else:
                options['came_from'] = came_from

            if login_status is None:
                login_status = req.form.get('login_status', None)
            if login_status is not None:
                options['login_status'] = login_status
            url = mangle.urlencode(url, **options)
            resp.redirect(url, lock=1)
            return 1

        # Could not challenge.
        return 0

    security.declarePrivate('updateCredentials')
    def updateCredentials(self, request, response, login, new_password):
        """ Respond to change of credentials (NOOP for basic auth). """
        cookie_str = '%s:%s' % (login.encode('hex'), new_password.encode('hex'))
        cookie_val = encodestring(cookie_str)
        cookie_val = cookie_val.rstrip()
        expires = rfc1123_date(time.time() + self.lifetime)
        response.setCookie(self.cookie_name, quote(cookie_val), path='/',
            expires=expires)

    security.declarePublic('login')
    def login(self):
        """ Set a cookie and redirect to the url that we tried to
        authenticate against originally.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        login = request.get('__ac_name', '')
        password = request.get('__ac_password', '')

        if (not login) or (not password):
            return self.unauthorized(
                login_status=u"You need to type a login and a password.")
        else:
            creds = {'login': login, 'password': password,}
            pas_instance = self._getPAS()
            if pas_instance is not None:
                plugins = pas_instance.plugins
                authenticators = plugins.listPlugins(IAuthenticationPlugin)
                for auth_id, auth in authenticators:
                    try:
                        uid_and_info = auth.authenticateCredentials(creds)
                        if uid_and_info is None:
                            continue
                        user_id, info = uid_and_info
                        if user_id is not None:
                            pas_instance.updateCredentials(request, response,
                                                           login, password)
                            break
                    except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                        continue

            # Default to virtual host root
            url = find_root(self).absolute_url()
            if self.redirect_to_path:
                came_path = request.form.get('came_path')
                if came_path is not None:
                    url = urlparse.urlunparse(
                        urlparse.urlparse(url)[:2] +
                        urlparse.urlparse(came_path)[2:])
            else:
                came_from = request.form.get('came_from')
                if came_from is not None:
                    url = came_from
            return response.redirect(url)


InitializeClass(SilvaCookieAuthHelper)

