# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import unittest

from Products.Silva import roleinfo
from Products.PluggableAuthService.interfaces import plugins
from zope.component import queryUtility
from zope.interface.verify import verifyObject

from silva.core.services import interfaces
from silva.core.interfaces.auth import IGroup, IMember
from silva.pas.base.testing import FunctionalLayer


class ServiceTestCase(unittest.TestCase):
    """Test case for PAS install/deinstall.
    """
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')

        # Add a test user.
        pas_acl = self.root.acl_users
        pas_acl._doAddUser('luser', 'luser', [], [])

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
        self.assertEqual(service, self.root.service_members)
        self.assertTrue(verifyObject(interfaces.IMemberService, service))

        service = queryUtility(interfaces.IGroupService)
        self.assertEqual(
            service.meta_type,
            "Silva Pluggable Auth Service Member Service")
        self.assertEqual(service, self.root.service_members)
        #self.assertTrue(verifyObject(interfaces.IGroupService, service))

    def test_acl_user(self):
        """Verify that a the acl_users have been added and configured
        by the installation script.
        """
        # And a acl_users set
        pas_acl = self.root.acl_users
        self.assertEqual(
            pas_acl.objectIds(),
            ['plugins', 'cookie_auth', 'users', 'roles', 'zope'])

        # As well, Silva roles should be loaded in PAS (Owner is set
        # by default in PAS).
        self.assertEqual(
            set(p['id'] for p in pas_acl.roles.enumerateRoles()),
            set(('Owner',) + roleinfo.ASSIGNABLE_ROLES))

    def test_invalid_member(self):
        """Looking for a users that doesn't exists won't return anything.
        """
        service = queryUtility(interfaces.IMemberService)
        self.assertEqual(service.is_user('winner'), False)
        self.assertEqual(service.get_member('winner'), None)
        self.assertEqual(service.find_members('winner'), [])

    def test_valid_member(self):
        """Looking for a member will actually return one.
        """
        service = queryUtility(interfaces.IMemberService)
        self.assertEqual(service.is_user('luser'), True)

        member = service.get_member('luser')
        self.assertNotEqual(member, None)
        self.assertEqual(member.userid(), 'luser')
        self.assertEqual(member.fullname(), 'luser')
        self.assertTrue(verifyObject(IMember, member))

        self.assertEqual(service.find_members('luser'), [member])

    def test_valid_acquired_member(self):
        """Look for a member that is not defined in the site
        acl_users, but at the root of Zope. It should by found with
        the help of the cascading plugin.
        """
        service = queryUtility(interfaces.IMemberService)
        self.assertEqual(service.is_user('manager'), True)

        member = service.get_member('manager')
        self.assertNotEqual(member, None)
        self.assertEqual(member.userid(), 'manager')
        self.assertEqual(member.fullname(), 'manager')
        self.assertTrue(verifyObject(IMember, member))

        self.assertEqual(service.find_members('manager'), [member])

    def test_group_disable_by_default(self):
        """By default there is no group source, so group are not
        activated.
        """
        service = queryUtility(interfaces.IGroupService)
        self.assertEqual(service.use_groups(), False)


class GroupEnabledServiceTestCase(unittest.TestCase):
    """Test case for PAS install/deinstall.
    """
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')

        # Add and configure a group backend in the acl_users
        pas_acl = self.root.acl_users
        factory = pas_acl.manage_addProduct['PluggableAuthService']
        factory.addZODBGroupManager('groups')
        pas_acl.groups.addGroup('losers', 'Losing users')
        pas_acl.plugins.activatePlugin(
            plugins.IGroupEnumerationPlugin, 'groups')

    def test_invalid_group(self):
        """Looking for a group that doesn't exists won't return
        anything.
        """
        service = queryUtility(interfaces.IGroupService)

        # So now groups should be on
        self.assertEqual(service.use_groups(), True)

        # If a group doesn't exists you won't find it.
        self.assertEqual(service.is_group('winners'), False)
        self.assertEqual(service.get_group('winners'), None)
        self.assertEqual(service.find_groups('winners'), [])

    def test_valid_group(self):
        """Looking for a valid group will return something.
        """
        service = queryUtility(interfaces.IGroupService)

        # So now groups should be on
        self.assertEqual(service.use_groups(), True)

        # If a group doesn't exists you won't find it.
        self.assertEqual(service.is_group('losers'), True)

        group = service.get_group('losers')
        self.assertNotEqual(group, None)
        self.assertEqual(group.groupid(), 'losers')
        self.assertEqual(group.groupname(), 'Losing users')
        self.assertTrue(verifyObject(IGroup, group))
        self.assertEqual(len(service.find_groups('losers')), 1)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    suite.addTest(unittest.makeSuite(GroupEnabledServiceTestCase))
    return suite
