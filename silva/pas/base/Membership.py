# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

# Zope
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Acquisition import aq_base, aq_inner, aq_parent
import Globals

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit

from Products.Silva.interfaces import IMember
from Products.Silva.SimpleMembership import SimpleMemberService

from Products.PluggableAuthService.interfaces.authservice import IPluggableAuthService

import types
import urlparse

from zope.interface import implements
from interfaces import IPASMemberService


class MemberService(SimpleMemberService):
    security = ClassSecurityInfo()

    implements(IPASMemberService)

    meta_type = 'Silva Pluggable Auth Service Member Service'
    title = 'Silva Pluggable Auth Service Membership Service'

    _use_direct_lookup = False

    # ZMI configuration  

    security.declareProtected('View management screens', 'manage_editForm')
    manage_editForm = PageTemplateFile(
        'www/memberServiceEdit', globals(),  __name__='manage_editForm')


    security.declareProtected('View management screens',
                              'manage_editServiceSettings')
    def manage_editServiceSettings(self, REQUEST):
        """manage method to edit service settings"""
        allow_auth_requests = int(REQUEST['allow_authentication_requests'])
        self.set_allow_authentication_requests(allow_auth_requests)
        self.set_use_direct_lookup(int(REQUEST['use_direct_lookup']))
        return self.manage_editForm(manage_tabs_message='Changed settings')


    security.declareProtected(SilvaPermissions.ChangeSilvaAccess,
                              'set_use_direct_lookup')
    def set_use_direct_lookup(self, value):
        """sets use_direct_lookup"""
        self._use_direct_lookup = value


    security.declareProtected(SilvaPermissions.ReadSilvaContent,
                              'use_direct_lookup')
    def use_direct_lookup(self):
        return self._use_direct_lookup


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_user')
    def is_user(self, userid):
        """Check if the given user is a PAS user.
        """
        if self.use_direct_lookup():
            return True

        root = self.get_root()
        pas = getattr(root, 'acl_users')
        return (len(pas.searchUsers(exact_match=True, id=userid)) == 1)


    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'find_members')
    def find_members(self, search_string):
        """Search for members
        """
        root = self.get_root()
        pas = getattr(root, 'acl_users')
        members = getattr(root, 'Members')
        
        users = pas.searchUsers(id=search_string, exact_match=False)
        result = []
        for user in users:
            id = user['userid']
            member = getattr(members, id, None)
            if member is None:
                members.manage_addProduct['Silva'].manage_addSimpleMember(id)
                member = getattr(members, id)
            result.append(member.__of__(self))
            
        return result


Globals.InitializeClass(MemberService)

manage_addMemberServiceForm = PageTemplateFile(
    "www/memberServiceAdd", globals(),
    __name__='manage_addMemberServiceForm')

def manage_addMemberService(self, id, REQUEST=None):
    """Add a Member Service."""
    object = MemberService(id)
    self._setObject(id, object)
    add_and_edit(self, id, REQUEST)
    return ''
