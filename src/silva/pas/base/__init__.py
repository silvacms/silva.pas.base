# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from silva.pas.base import install
from silva.pas.base.plugins import cookie, cascading
from silva.core import conf as silvaconf

from Products.PluggableAuthService.PluggableAuthService import \
    registerMultiPlugin
from AccessControl.Permissions import manage_users as ManageUsers

registerMultiPlugin(cookie.SilvaCookieAuthHelper.meta_type)
registerMultiPlugin(cascading.SilvaCascadingPASPlugin.meta_type)

silvaconf.extensionName('silva.pas.base')
silvaconf.extensionTitle('Silva Pluggable Auth Service Support')


def initialize(context):
    context.registerClass(
        cookie.SilvaCookieAuthHelper,
        permission=ManageUsers,
        constructors=
        (cookie.manage_addSilvaCookieAuthHelperForm,
         cookie.manage_addSilvaCookieAuthHelper),
        visibility=None,
        icon="www/cookie.png")
    context.registerClass(
        cascading.SilvaCascadingPASPlugin,
        permission=ManageUsers,
        constructors=
        (cascading.manage_addSilvaCascadingPASPluginForm,
         cascading.manage_addSilvaCascadingPASPlugin),
        visibility=None,
        icon="www/cascading.png")


CLASS_CHANGES = {
    'silva.core.pas.interfaces IPASMemberService':
        'silva.core.pas.interfaces IPASService',
    }
