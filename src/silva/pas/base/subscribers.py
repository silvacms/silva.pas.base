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
        factory = root.manage_addProduct['BTreeFolder2']
        factory.manage_addBTreeFolder('Members')

    if 'acl_users' not in installed_ids:
        create_acl_users(root)


def create_acl_users(folder):
    """Create a acl_users in the given folder.
    """
    factory = folder.manage_addProduct['PluggableAuthService']
    factory.addPluggableAuthService()
    acl_users = folder._getOb('acl_users')
    # Add cookie storage for auth
    factory = acl_users.manage_addProduct['silva.pas.base']
    factory.manage_addSilvaCookieAuthHelper('cookie_auth')

    # Add a user and rolesource
    factory = acl_users.manage_addProduct['PluggableAuthService']
    factory.addZODBUserManager('users')
    factory.addZODBRoleManager('roles')
    # Add a delegating source, to ask users to default Zope ACL
    factory.manage_addDelegatingMultiPlugin(
        'zope', delegate_path='/acl_users')

    # Configure plugins
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

    # Configure Silva roles.
    create_silva_roles(acl_users.roles)


def create_silva_roles(plugin):
    """Create default Silva roles in the roles assigner plugin.
    """
    existing = [r['id'] for r in plugin.enumerateRoles()]
    blacklist = ['Anonymous', 'Authenticated',]
    to_create = set(plugin.validRoles()).difference(existing + blacklist)

    for role in to_create:
        plugin.addRole(role)


if __name__ == '__main__':
    print """This module is not an installer. You don't have to run it."""
