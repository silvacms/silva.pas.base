# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import install
import Membership

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.PluggableAuthService.PluggableAuthService import \
    registerMultiPlugin
from AccessControl.Permissions import manage_users as ManageUsers
from plugins import cookie, cascading

registerMultiPlugin(cookie.SilvaCookieAuthHelper.meta_type)
registerMultiPlugin(cascading.SilvaCascadingPASPlugin.meta_type)

def initialize(context):
    extensionRegistry.register(
        'silva.pas.base', 'Silva Pluggable Auth Service Support', context, [],
        install, depends_on='Silva')
    context.registerClass(
        Membership.MemberService,
        constructors = (Membership.manage_addMemberServiceForm,
                        Membership.manage_addMemberService),
        )
    context.registerClass(
        cookie.SilvaCookieAuthHelper,
        permission=ManageUsers,
        constructors=
        (cookie.manage_addSilvaCookieAuthHelperForm,
         cookie.manage_addSilvaCookieAuthHelper),
        visibility=None)
    context.registerClass(
        cascading.SilvaCascadingPASPlugin,
        permission=ManageUsers,
        constructors=
        (cascading.manage_addSilvaCascadingPASPluginForm,
         cascading.manage_addSilvaCascadingPASPlugin),
        visibility=None)


