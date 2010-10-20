# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from Acquisition import aq_base
from Products.Silva import roleinfo
from zope.component import queryUtility
from zope.interface.verify import verifyObject

from silva.core.services import interfaces
from silva.pas.base.testing import FunctionalLayer


class ServiceTestCase(unittest.TestCase):
    """Test case for PAS install/deinstall.
    """
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')

    def test_service(self):
        """Install should change the members services and set up an
        acl_user.
        """
        # First the extension should be installed and installed
        service_extensions = self.root.service_extensions
        self.assertTrue(service_extensions.is_installed('silva.pas.base'))

        service = queryUtility(interfaces.IMemberService)
        self.assertEqual(service, self.root.service_members)
        self.assertEqual(
            service.meta_type,
            "Silva Pluggable Auth Service Member Service")
        self.assertTrue(verifyObject(interfaces.IMemberService, service))
        #self.assertTrue(verifyObject(interfaces.IGroupService, service))

    def test_acl_user(self):
        # And a acl_users set
        self.assertTrue(hasattr(aq_base(self.root), 'acl_users'))
        pas_acl = self.root.acl_users
        self.assertEqual(
            pas_acl.objectIds(),
            ['plugins', 'cookie_auth', 'users', 'roles', 'zope'])

        # As well, Silva roles should be loaded in PAS (Owner is set
        # by default in PAS).
        self.assertEqual(
            set(p['id'] for p in pas_acl.roles.enumerateRoles()),
            set(('Owner',) + roleinfo.ASSIGNABLE_ROLES))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    return suite
