# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urllib

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

# Silva
from Products.Silva import SilvaPermissions, mangle
from Products.Silva.SimpleMembership import SimpleMemberService

from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService

from zope.interface import implements
from zope.component import getUtilitiesFor
from silva.pas.base.interfaces import IPASMemberService, IUserConverter
from silva.core import conf as silvaconf


class MemberService(SimpleMemberService):
    """Silva Member Service who delagates members search to PAS.
    """
    security = ClassSecurityInfo()
    implements(IPASMemberService)

    meta_type = 'Silva Pluggable Auth Service Member Service'
    title = 'Silva Pluggable Auth Service Membership Service'

    silvaconf.icon('www/members.png')

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


    def _clean_id(self, userid):
        for utility in getUtilitiesFor(IUserConverter):
            converter = utility[1]()
            if converter.match(userid):
                return converter.convert(userid)
        return userid           # No transformation, return the
                                # default one.


    def _getPAS(self, location=None):
        if location is None:
            location = self.get_root()
        pas = getattr(location, 'acl_users')
        if not IPluggableAuthService.providedBy(pas):
            raise RuntimeError, "Expect to be used with a PAS acl user"
        return pas


    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'get_member')
    def get_member(self, userid, location=None):
        return super(MemberService, self).get_member(
            self._clean_id(userid), location=location)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              'is_user')
    def is_user(self, userid, location=None):
        """Check if the given user is a PAS user.
        """
        if self.use_direct_lookup():
            return not (userid is None)

        pas = self._getPAS(location=location)
        # If you use the silva membership user enumerater, you can get
        # more than one user found.
        return (len(pas.searchUsers(exact_match=True,
                                    id=self._clean_id(userid))) > 0)


    security.declareProtected(SilvaPermissions.ApproveSilvaContent,
                              'find_members')
    def find_members(self, search_string, location=None):
        """Search for members
        """
        root = self.get_root()
        pas = self._getPAS(location=location)
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


    security.declarePublic('logout')
    def logout(self, came_from=None, REQUEST=None):
        """Logout the current user.
        """
        if REQUEST is None and hasattr(self, REQUEST):
            REQUEST = self.REQUEST
        if REQUEST is None:
            return

        root = self.get_root()
        pas = getattr(root, 'acl_users')
        pas.resetCredentials(REQUEST, REQUEST.RESPONSE)
        if came_from is None:
            came_from = REQUEST.form.get('came_from', None)
            if came_from:
                came_from = urllib.unquote(came_from)
        if came_from is not None:
            exit_url = came_from
        else:
            exit_url = root.absolute_url()

        exit_url = mangle.urlencode(
            exit_url, login_status=u"You have been logged out.")
        REQUEST.RESPONSE.redirect(exit_url)


InitializeClass(MemberService)
