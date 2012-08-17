# -*- coding: utf-8 -*-
# Copyright (c) 2008-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from Products.PluggableAuthService.interfaces import plugins as pas
from silva.core.interfaces import IRoot
from silva.core.interfaces import IInstallRootEvent

@grok.subscribe(IRoot, IInstallRootEvent)
def configure_service(root, event):
    installed_ids = root.objectIds()

    if 'Members' not in installed_ids:
        root.manage_addProduct['BTreeFolder2'].manage_addBTreeFolder('Members')

    if 'acl_users' in installed_ids:
        # if there is another user folder already available, don't touch it
        return

    root.manage_addProduct['PluggableAuthService'].addPluggableAuthService()
    acl_users = root.acl_users
    factory = acl_users.manage_addProduct['silva.pas.base']
    # Add cookie storage for auth
    factory.manage_addSilvaCookieAuthHelper('cookie_auth')
    factory = acl_users.manage_addProduct['PluggableAuthService']
    # Add a user source
    factory.addZODBUserManager('users')
    # Add a role source
    factory.addZODBRoleManager('roles')
    # Add a delegating source, to ask users to default Zope ACL
    factory.manage_addDelegatingMultiPlugin(
        'zope', delegate_path='/acl_users')

    plugins = acl_users.plugins
    plugins.activatePlugin(pas.IExtractionPlugin, 'cookie_auth')
    plugins.activatePlugin(pas.IChallengePlugin, 'cookie_auth')
    plugins.activatePlugin(pas.ICredentialsResetPlugin, 'cookie_auth')
    plugins.activatePlugin(pas.IAuthenticationPlugin, 'cookie_auth')
    plugins.activatePlugin(pas.IAuthenticationPlugin, 'users')
    plugins.activatePlugin(pas.IAuthenticationPlugin, 'zope')
    plugins.activatePlugin(pas.IUserAdderPlugin, 'users')
    plugins.activatePlugin(pas.IUserEnumerationPlugin, 'users')
    plugins.activatePlugin(pas.IUserEnumerationPlugin, 'zope')
    plugins.activatePlugin(pas.IRolesPlugin, 'roles')
    plugins.activatePlugin(pas.IRolesPlugin, 'zope')
    plugins.activatePlugin(pas.IRoleAssignerPlugin, 'roles')
    plugins.activatePlugin(pas.IRoleEnumerationPlugin, 'roles')

    createDefaultSilvaRolesInPAS(acl_users.roles)


def createDefaultSilvaRolesInPAS(plugin):
    """Create default Silva roles in the roles assigner plugin.
    """
    existing = [r['id'] for r in plugin.enumerateRoles()]
    blacklist = ['Anonymous', 'Authenticated',]
    to_create = set(plugin.validRoles()).difference(existing + blacklist)

    for role in to_create:
        plugin.addRole(role)


def registerServiceMembers(root):
    if 'service_members' in root.objectIds():
        root.manage_delObjects(['service_members',])
    factory = root.manage_addProduct['silva.pas.base']
    factory.manage_addMemberService('service_members')


if __name__ == '__main__':
    print """This module is not an installer. You don't have to run it."""
