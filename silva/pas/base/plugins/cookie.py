# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.PluggableAuthService.plugins.CookieAuthHelper import CookieAuthHelper
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
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

    def unauthorized(self, extra=None):
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
                query = req.get('QUERY_STRING')
                if query:
                    if not query.startswith('?'):
                        query = '?' + query
                    came_from = came_from + query
            else:
                req_url = req.get('URL', '')

                if req_url and req_url == url:
                    return 0

            url = url + '?came_from=%s' % quote(came_from)
            if extra:
                url = url + '&login_status=%s' % quote(extra)
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
            return self.unauthorized(extra="You need to type a login and a password.")
        else:
            pas_instance = self._getPAS()
            if pas_instance is not None:
                pas_instance.updateCredentials(request, response, 
                                               login, password)

            came_from = request.form['came_from']
            return response.redirect(came_from)


InitializeClass(SilvaCookieAuthHelper)

