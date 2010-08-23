# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.PluggableAuthService.interfaces.plugins import *
from silva.pas.base.interfaces import IPASMemberService


def install(root):
    """Install PAS Support.
    """
    # set up acl_users if needed
    registerUserFolder(root)

    # set up service_members if needed
    registerServiceMembers(root)


def uninstall(root):
    """Uninstall PAS Support.
    """
    # remove special member service and install default silva one
    root.manage_delObjects(['service_members',])
    factory = root.manage_addProduct['Silva']
    factory.manage_addSimpleMemberService('service_members')


def is_installed(root):
    return IPASMemberService.providedBy(root.service_members)


def registerUserFolder(root):
    # if there is another user folder already available, don't touch it
    if getattr(root.aq_base, 'acl_users', None) is not None:
        return

    root.manage_addProduct['PluggableAuthService'].addPluggableAuthService()
    acl_users = root.acl_users
    add_product = acl_users.manage_addProduct['silva.pas.base']
    # Add cookie storage for auth
    add_product.manage_addSilvaCookieAuthHelper('cookie_auth')
    add_product = acl_users.manage_addProduct['PluggableAuthService']
    # Add a user source
    add_product.addZODBUserManager('users')
    # Add a role source
    add_product.addZODBRoleManager('roles')
    # Add a delegating source, to ask users to default Zope ACL
    add_product.manage_addDelegatingMultiPlugin('zope',
                                                delegate_path='/acl_users')

    plugins = acl_users.plugins
    plugins.activatePlugin(IExtractionPlugin, 'cookie_auth')
    plugins.activatePlugin(IChallengePlugin, 'cookie_auth')
    plugins.activatePlugin(ICredentialsResetPlugin, 'cookie_auth')
    plugins.activatePlugin(ICredentialsUpdatePlugin, 'cookie_auth')
    plugins.activatePlugin(IAuthenticationPlugin, 'users')
    plugins.activatePlugin(IAuthenticationPlugin, 'zope')
    plugins.activatePlugin(IUserAdderPlugin, 'users')
    plugins.activatePlugin(IUserEnumerationPlugin, 'users')
    plugins.activatePlugin(IUserEnumerationPlugin, 'zope')
    plugins.activatePlugin(IRolesPlugin, 'roles')
    plugins.activatePlugin(IRolesPlugin, 'zope')
    plugins.activatePlugin(IRoleAssignerPlugin, 'roles')
    plugins.activatePlugin(IRoleEnumerationPlugin, 'roles')

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
    root.manage_delObjects(['service_members'])
    add_product = root.manage_addProduct['silva.pas.base']
    add_product.manage_addMemberService('service_members')


if __name__ == '__main__':
    print """This module is not an installer. You don't have to run it."""
