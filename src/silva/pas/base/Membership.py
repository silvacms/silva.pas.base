# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import urllib

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

# Silva
from Products.Silva import SilvaPermissions, mangle
from Products.Silva.SimpleMembership import SimpleMemberService
from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import \
    IGroupEnumerationPlugin

from five import grok
from silva.core import conf as silvaconf
from silva.core.views import views as silvaviews
from silva.core.interfaces.auth import IGroup
from silva.pas.base.interfaces import IPASService, IUserConverter
from zope.component import getUtilitiesFor


class Group(object):
    grok.implements(IGroup)

    def __init__(self, groupid, groupname):
        self.__groupid = groupid
        self.__groupname = groupname

    def groupid(self):
        return self.__groupid

    def groupname(self):
        return self.__groupname



class MemberService(SimpleMemberService):
    """Silva Member Service who delagates members search to PAS.
    """
    security = ClassSecurityInfo()
    grok.implements(IPASService)

    meta_type = 'Silva Pluggable Auth Service Member Service'
    title = 'Silva Pluggable Auth Service Membership Service'

    silvaconf.icon('Membership.png')

    def _convert_userid(self, userid):
        for name, utility in getUtilitiesFor(IUserConverter):
            converter = utility()
            if converter.match(userid):
                return converter.convert(userid)
        return userid           # No transformation, return the
                                # default one.

    def _get_pas(self, location=None):
        if location is None:
            location = self.get_root()
        pas = getattr(location, 'acl_users')
        if not IPluggableAuthService.providedBy(pas):
            raise RuntimeError, "Expect to be used with a PAS acl user"
        return pas

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_member')
    def get_member(self, userid, location=None):
        return super(MemberService, self).get_member(
            self._convert_userid(userid), location=location)

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'is_user')
    def is_user(self, userid, location=None):
        """Check if the given user is a PAS user.
        """
        pas = self._get_pas(location=location)
        # If you use the silva membership user enumerater, you can get
        # more than one user found.
        return (len(pas.searchUsers(
                    exact_match=True, id=self._convert_userid(userid))) > 0)

    security.declareProtected(
        SilvaPermissions.ApproveSilvaContent, 'find_members')
    def find_members(self, search_string, location=None):
        """Search for members
        """
        root = self.get_root()
        pas = self._get_pas(location=location)
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

    security.declareProtected(
        SilvaPermissions.ApproveSilvaContent, 'find_groups')
    def find_groups(self, search_string, location=None):
        """Search for members
        """
        pas = self._get_pas(location=location)
        groups = pas.searchGroups(id=search_string, exact_match=False)
        result = []
        for group in groups:
            result.append(Group(group['groupid'], group['title']))
        return result

    security.declareProtected(
        SilvaPermissions.ApproveSilvaContent, 'use_groups')
    def use_groups(self, location=None):
        pas = self._get_pas(location=location)
        return len(pas.plugins.listPlugins(IGroupEnumerationPlugin)) != 0

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'is_group')
    def is_group(self, groupid, location=None):
        """Check if the given user is a PAS group.
        """
        pas = self._get_pas(location=location)
        # You can retrieve a group from multiple sources
        return (len(pas.searchGroups(exact_match=True, id=groupid)) > 0)

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_group')
    def get_group(self, groupid, location=None):
        pas = self._get_pas(location=location)
        # You can retrieve a group from multiple sources
        groups = pas.searchGroups(exact_match=True, id=groupid)
        if not groups:
            return None
        return Group(groups[0]['groupid'], groups[0]['title'])

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


class LoginPage(silvaviews.Page):
    grok.name('silva_login_form.html')
