from Products.Silva.install import add_helper, zpt_add_helper
from Products.PluggableAuthService.interfaces.plugins import *

from interfaces import IPASMemberService

def install(root):
    """Install PAS Support.
    """
    # add login form
    add_helper(root, 'silva_login_form.html', globals(), zpt_add_helper, 0)

    # set up acl_users if needed
    registerUserFolder(root)

    # set up service_members if needed
    registerServiceMembers(root)
    
def uninstall(root):
    # remove special member service and install default silva one
    root.manage_delObjects(['service_members', 'silva_login_form.html'])
    root.manage_addProduct['Silva'].manage_addSimpleMemberService('service_members')
    
def is_installed(root):
    return IPASMemberService.providedBy(root.service_members)

def registerViews(reg):
    """Register core views on registry.
    """
    pass

def unregisterViews(reg):
    """Unregister core views on registry.
    """
    pass

def registerUserFolder(root):
    # if there is another user folder already available, don't touch it
    if getattr(root.aq_base, 'acl_users', None) is not None:
        return

    root.manage_addProduct['PluggableAuthService'].addPluggableAuthService()
    acl_users = root.acl_users
    acl_users.manage_addProduct['PluggableAuthService'].addCookieAuthHelper('cookie_auth', 
                                                                            cookie_name='__ac_silva')
    acl_users.cookie_auth.login_path = 'silva_login_form.html'
    acl_users.manage_addProduct['PluggableAuthService'].addZODBUserManager('users')
    acl_users.manage_addProduct['PluggableAuthService'].addZODBRoleManager('roles')

    plugins = acl_users.plugins
    plugins.activatePlugin(IExtractionPlugin, 'cookie_auth')
    plugins.activatePlugin(IChallengePlugin, 'cookie_auth')
    plugins.activatePlugin(ICredentialsResetPlugin, 'cookie_auth')
    plugins.activatePlugin(ICredentialsUpdatePlugin, 'cookie_auth')
    plugins.activatePlugin(IAuthenticationPlugin, 'users')
    plugins.activatePlugin(IUserAdderPlugin, 'users')
    plugins.activatePlugin(IUserEnumerationPlugin, 'users')
    plugins.activatePlugin(IRolesPlugin, 'roles')
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
    root.manage_addProduct['silva.pas.base'].manage_addMemberService(
        'service_members')
    




if __name__ == '__main__':
    print """This module is not an installer. You don't have to run it."""
