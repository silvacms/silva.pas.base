# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.PluggableAuthService.interfaces import plugins

class ICookiePlugin(
    plugins.IAuthenticationPlugin,
    plugins.IExtractionPlugin,
    plugins.IChallengePlugin,
    plugins.ICredentialsResetPlugin):
    pass
