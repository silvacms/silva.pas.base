from Products.FileSystemSite.DirectoryView import manage_addDirectoryView
from Products.Silva.install import add_fss_directory_view

from Products.PluggableAuthService.interfaces.plugins import *

def install(root):
    """The view infrastructure for SilvaExtETHLDAP.
    """
    # create the core views from filesystem
    add_fss_directory_view(root.service_views, 'silva.pas.base',
                           __file__, 'views')
    # also register views
    registerViews(root.service_view_registry)

    # set up acl_users if needed
    registerUserFolder(root)

    # set up service_members if needed
    registerServiceMembers(root)
    
def uninstall(root):
    unregisterViews(root.service_view_registry)
    root.service_views.manage_delObjects(['silva.pas.base'])
    # remove special member service and install default silva one
    root.manage_delObjects(['service_members'])
    root.manage_addProduct['Silva'].manage_addSimpleMemberService(
        'service_members')
    
def is_installed(root):
    return hasattr(root.service_views, 'silva.pas.base')

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
    acl_users.manage_addProduct['PluggableAuthService'].addZODBUserManager('users')
    acl_users.manage_addProduct['PluggableAuthService'].addZODBRoleManager('roles')

    plugins = acl_users.plugins
    plugins.activatePlugin(IExtractionPlugin, 'cookie_auth')
    plugins.activatePlugin(IChallengePlugin, 'cookie_auth')
    plugins.activatePlugin(ICredentialsResetPlugin, 'cookie_auth')
    plugins.activatePlugin(ICredentialsUpdatePlugin, 'cookie_auth')
    plugins.activatePlugin(IAuthenticationPlugin, 'users')
    plugins.activatePlugin(IUserEnumerationPlugin, 'users')
    plugins.activatePlugin(IRolesPlugin, 'roles')
    plugins.activatePlugin(IRoleEnumerationPlugin, 'roles')

def registerServiceMembers(root):
    root.manage_delObjects(['service_members'])
    root.manage_addProduct['silva.pas.base'].manage_addMemberService(
        'service_members')
    
if __name__ == '__main__':
    print """This module is not an installer. You don't have to run it."""
