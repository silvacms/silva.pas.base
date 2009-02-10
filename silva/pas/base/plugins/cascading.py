# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import implements

from Products.PluggableAuthService.plugins.SearchPrincipalsPlugin import \
    SearchPrincipalsPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IAuthenticationPlugin, IRolesPlugin, IGroupsPlugin, IPropertiesPlugin
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from AccessControl.SecurityInfo import ClassSecurityInfo
from Globals import InitializeClass


def manage_addSilvaCascadingPASPlugin(self, id, title='',
                                      delegate_path='',
                                      REQUEST=None, **kw):
    """Create an instance of an Silva cascading PAS plugin.
    """

    o = SilvaCascadingPASPlugin(id, title, delegate_path, **kw)
    self._setObject(o.getId(), o)

    if REQUEST is not None:
        REQUEST["RESPONSE"].redirect("%s/manage_workspace"
                "?manage_tabs_message=Silva+cascading+PAS+plugin+added." %
                self.absolute_url())


manage_addSilvaCascadingPASPluginForm =  \
    PageTemplateFile("../www/cascadingAddForm", globals(),
                     __name__="manage_addSilvaCascadingPASPluginForm")


class SilvaCascadingPASPlugin(SearchPrincipalsPlugin):

    meta_type = 'Silva Cascading PAS Plugin'
    security = ClassSecurityInfo()

    implements(IAuthenticationPlugin, IRolesPlugin, IGroupsPlugin, \
                   IPropertiesPlugin)

    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """See IAuthenticationPlugin
        """
        acl = self._getDelegate()
        if acl is None:
            return None

        plugins = acl['plugins']
        authenticators = plugins.listPlugins(IAuthenticationPlugin)
        for authenticator_id, auth in authenticators:
            uid_and_info = auth.authenticateCredentials(credentials)
            if uid_and_info is not None:
                return uid_and_info
        return None

    security.declarePrivate('getPropertiesForUser')
    def getPropertiesForUser(self, user, request=None):
        """See IPropertiesPlugin
        """
        acl = self._getDelegate()
        if acl is None:
            return {}

        plugins = acl['plugins']
        properties = plugins.listPlugins(IPropertiesPlugin)
        for property_id, prop in properties:
            info = prop.getPropertiesForUser(user, request)
            if info:
                return info
        return {}

    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):
        """See IRolesPlugin
        """
        acl = self._getDelegate()
        if acl is None:
            return ()

        roles = []
        plugins = acl['plugins']
        rolemakers = plugins.listPlugins(IRolesPlugin)
        for rolemaker_id, rolemaker in rolemakers:
            news = rolemaker.getRolesForPrincipal(principal, request)
            if news:
                roles.extend(news)
        return roles

    security.declarePrivate('getGroupsForPrincipal')
    def getGroupsForPrincipal(self, principal, request=None):
        """See IGroupsPlugin
        """
        acl = self._getDelegate()
        if acl is None:
            return ()

        groups = []
        plugins = acl['plugins']
        groupmakers = plugins.listPlugins(IGroupsPlugin)
        for groupmaker_id, groupmaker in groupmakers:
            news = groupmaker.getGroupsForPrincipal(principal, request)
            if news:
                groups.extend(news)
        return groups


InitializeClass(SilvaCascadingPASPlugin)



