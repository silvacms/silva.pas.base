import install
import Membership

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.FileSystemSite.DirectoryView import registerDirectory

def initialize(context):
    extensionRegistry.register(
        'silva.pas.base', 'Silva Pluggable Auth Service Support', context, [],
        install, depends_on='Silva')
    
    context.registerClass(
        Membership.MemberService,
        constructors = (Membership.manage_addMemberServiceForm,
                        Membership.manage_addMemberService),
        )

    registerDirectory('views', globals())
