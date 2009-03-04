# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.PluggableAuthService.PluggableAuthService import \
    _SWALLOWABLE_PLUGIN_EXCEPTIONS
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin
from Products.PluggableAuthService.plugins.CookieAuthHelper import \
    CookieAuthHelper
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Silva import mangle
from AccessControl.SecurityInfo import ClassSecurityInfo
from Globals import InitializeClass

from urllib import quote

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


class SilvaCookieAuthHelper(CookieAuthHelper):

    meta_type = 'Silva Cookie Auth Helper'
    security = ClassSecurityInfo()

    # Customize configuration
    cookie_name='__ac_silva'
    login_path = 'silva_login_form.html'


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
                came_from = req.get('URL', '')
                query = req.form.copy()
                if query:
                    if 'login_status' in query:
                        del query['login_status']
                    came_from = mangle.urlencode(came_from, **query)
            else:
                req_url = req.get('URL', '')

                if req_url and req_url == url:
                    return 0

            options = {}
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

            came_from = request.form['came_from']
            return response.redirect(came_from)


InitializeClass(SilvaCookieAuthHelper)

