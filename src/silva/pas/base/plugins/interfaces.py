# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from Products.PluggableAuthService.interfaces import plugins


class ICookiePlugin(
    plugins.IAuthenticationPlugin,
    plugins.IExtractionPlugin,
    plugins.IChallengePlugin,
    plugins.ICredentialsUpdatePlugin,
    plugins.ICredentialsResetPlugin):
    pass
