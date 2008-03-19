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


# False interface to test if a container is a user folder.
class _IUserFolder:
    def providedBy(self, maybe_user_folder):
        return getattr(maybe_user_folder, 'getUser', None) is not None
IUserFolder = _IUserFolder()


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
        self.set_allow_authentication_requests(int(REQUEST['allow_authentication_requests']))
        self.set_use_direct_lookup(int(REQUEST['use_direct_lookup']))
        return self.manage_editForm(manage_tabs_message='Changed settings')


    security.declareProtected(SilvaPermissions.ChangeSilvaAccess,
                              'set_use_direct_lookup')
    def set_use_direct_lookup(self, value):
        """sets use_direct_lookup"""
        self._use_direct_lookup = value


    security.declarePrivate('_get_visible_user_folders')
    def _get_visible_user_folders(self):
        # lookup all user folders visible via acquisition
        # does something similar to RoleManager.get_valid_userids,
        # but tries to get rid of complicated acquisition pathes,
        # which I feel can only do harm here.
        # (deeply nested user folders are not really supported anyway)
        uf_list = []
        container = aq_inner(self)
        while container is not None:
            maybe_user_folder = getattr(aq_base(container), '__allow_groups__', None)
            if IUserFolder.providedBy(maybe_user_folder):
                uf_list.append(container.__allow_groups__)
            container = aq_inner(aq_parent(container))
        return uf_list


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_member')    
    def get_member(self, userid):
        if userid is None:
            # special case which might trigger an error,
            # as some user folders seem to return a not-None user
            # for a userid of None
            # I could not reproduce that, but with PAS, who knows what can happen ...
            return None
        for user_folder in self._get_visible_user_folders():
            user = user_folder.getUserById(userid)
            if user is not None:
                return self._get_known_member(userid, user_folder)
        return None


    security.declarePrivate('_create_new_member')
    def _create_new_member(self, userid, user_folder):
        # create a fresh member
        # this assumes the userid is valid and
        # the member does not exist yet
        members = aq_inner(self.Members)
        members.manage_addProduct['Silva'].manage_addSimpleMember(userid)
        member = getattr(members, userid)
        return member


    security.declarePrivate('_get_known_member')
    def _get_known_member(self, userid, user_folder):
        if not type(userid) in types.StringTypes:
            raise TypeError, 'the user id %s is no string but %s' % (userid, type(userid))
        # get member, add it if it doesn't exist yet
        # assumes userid is valid
        members = aq_inner(self.Members).aq_explicit
        member = getattr(members, userid, None)
        if member is None:
            member = self._create_new_member(userid, user_folder)
        assert IMember.providedBy(member)
        return member


    security.declareProtected(SilvaPermissions.ReadSilvaContent,
                              'use_direct_lookup')
    def use_direct_lookup(self):
        return self._use_direct_lookup


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_user')
    def is_user(self, userid):
        return self.use_direct_lookup() or not (self.get_member(userid) is None)


    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'find_members')
    def find_members(self, search_string):
        members = []
        for user_folder in self._get_visible_user_folders():
            # could use "adapters", except its probably overkill for now
            if IPluggableAuthService.providedBy(user_folder):
                result = user_folder.searchPrincipals(exact_match=False,
                                                      id=search_string)
                members.extend([ self._get_known_member(u['id'], user_folder)
                                 for u in result ])
            else:
                # something else: do it the old school way
                un = getattr(aq_base(user_folder), 'user_names', None)
                if callable(un):
                    result = user_folder.user_names()
                    members.extend([ self._get_known_member(uid, user_folder)
                                     for uid in result
                                     if uid.find(search_string) != -1])
        return members


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
