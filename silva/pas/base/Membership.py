# Zope
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import Globals

# Silva
from Products.Silva import SilvaPermissions
from Products.Silva.helpers import add_and_edit

from Products.Silva.SimpleMembership import SimpleMemberService
from Products.Silva.SimpleMembership import SimpleMember


import urlparse

class Member(SimpleMember):

    security = ClassSecurityInfo()

    meta_type = 'Silva Pluggable Auth Service Member'


Globals.InitializeClass(Member)

manage_addMemberForm = PageTemplateFile(
    "www/memberAdd", globals(),
    __name__='manage_addMemberForm')

def manage_addMember(self, id, REQUEST=None):
    """Add a Member."""
    object = Member(id)
    self._setObject(id, object)
    object.sec_assign(id, 'ChiefEditor')
    add_and_edit(self, id, REQUEST)
    return ''


class MemberService(SimpleMemberService):
    security = ClassSecurityInfo()

    meta_type = 'Silva Pluggable Auth Service Member Service'
    title = 'Silva Pluggable Auth Service Membership Service'

    security.declareProtected(SilvaPermissions.ReadSilvaContent,
                              'use_direct_lookup')
    def use_direct_lookup(self):
        return True

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_user')
    def is_user(self, userid):
        acl = self.aq_inner.acl_users
        return self.use_direct_lookup() or not (acl.getUserById(userid) is None)

    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'find_members')
    def find_members(self, search_string):
        acl = self.aq_inner.acl_users
        users = []
        for userid in acl.searchUsers(name=search_string, sort_by='id'):
            users.append(self.get_cached_member(userid))
        return users

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
