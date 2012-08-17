# -*- coding: utf-8 -*-
# Copyright (c) 2010-2012 Infrae. All rights reserved.
# See also LICENSE.txt

from Products.Silva.testing import SilvaLayer
import Products.GenericSetup.registry
from zope.testing import cleanup
import silva.pas.base
import transaction

# For incompetant useless Plone people.
cleanup.addCleanUp(Products.GenericSetup.registry._profile_registry.clear)


class SilvaPASLayer(SilvaLayer):
    default_products = SilvaLayer.default_products + [
        "GenericSetup",
        "PluggableAuthService",
        ]
    default_packages = SilvaLayer.default_packages + [
        "silva.pas.base",
        ]

    def _install_application(self, app):
        super(SilvaPASLayer, self)._install_application(app)
        app.root.service_extensions.install('silva.pas.base')
        transaction.commit()


FunctionalLayer = SilvaPASLayer(silva.pas.base)
