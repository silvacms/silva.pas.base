# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.Silva.tests import SilvaTestCase
from Products.Five import zcml

from Testing import ZopeTestCase as ztc


class PASTestCase(SilvaTestCase.SilvaTestCase):
    """Test case for PAS implementation.
    """


    def afterSetUp(self):
        """After set up, install the extension.
        """
        root = self.getRoot()
        root.service_extensions.install('silva.pas.base')

    def test_00install(self):
        """Install should change the members services and set up an
        acl_user.
        """
        root = self.getRoot()

        # First the extension should be installed
        service_extensions = root.service_extensions
        self.failUnless(service_extensions.is_installed('silva.pas.base'))

        # And a acl_users set 
        self.failUnless(hasattr(root.aq_base, 'acl_users'))
        pas_acl = root.acl_users
        default_plugins = ['plugins', 'cookie_auth', 'users', 'roles']
        self.assertEqual(pas_acl.objectIds(), default_plugins)

        # As well, Silva roles should be loaded in PAS (Owner is set
        # by default in PAS).
        pas_roles = set([p['id'] for p in pas_acl.roles.enumerateRoles()])
        expected_roles = set(['Owner',] + list(root.sec_get_roles()))
        self.assertEqual(pas_roles, expected_roles)



import unittest
def test_suite():
    
    # Load Five ZCML
    from Products import Five
    zcml.load_config('meta.zcml', Five)
    zcml.load_config('configure.zcml', Five)

    # Load our ZCML, which add the extension as a Product
    from silva.pas import base
    zcml.load_config('configure.zcml', base)

    # Load the Zope Product
    ztc.installProduct('GenericSetup')
    ztc.installProduct('PluginRegistry')
    ztc.installProduct('PluggableAuthService')
    ztc.installPackage('silva.pas.base')

    # Run tests
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PASTestCase))
    return suite