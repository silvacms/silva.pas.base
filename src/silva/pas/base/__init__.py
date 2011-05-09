# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from silva.pas.base.plugins import cookie, cascading
from silva.core import conf as silvaconf

from Products.PluggableAuthService.PluggableAuthService import \
    registerMultiPlugin
from AccessControl.Permissions import manage_users as ManageUsers

registerMultiPlugin(cookie.SilvaCookieAuthHelper.meta_type)
registerMultiPlugin(cascading.SilvaCascadingPASPlugin.meta_type)

silvaconf.extension_name('silva.pas.base')
silvaconf.extension_title('Silva Pluggable Auth Support')
silvaconf.extension_system()


def initialize(context):
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


CLASS_CHANGES = {
    'silva.core.pas.interfaces IPASMemberService':
        'silva.core.pas.interfaces IPASService',
    }
