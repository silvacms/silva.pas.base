# -*- coding: utf-8 -*-
# Copyright (c) 2008-2012 Infrae. All rights reserved.
# See also LICENSE.txt

import urllib

# Zope
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from zExceptions import BadRequest

# Silva
from Products.Silva import roleinfo
from Products.Silva import SilvaPermissions
from Products.Silva.SimpleMembership import SimpleMemberService
from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService
from Products.PluggableAuthService.interfaces.plugins import \
    IGroupEnumerationPlugin

from five import grok
from zope.component import getUtilitiesFor
from zope.component import queryMultiAdapter
from zope.interface import Interface
from zope import schema

from silva.core import conf as silvaconf
from silva.core.views import views as silvaviews
from silva.core.views.interfaces import IHTTPResponseHeaders
from silva.core.interfaces.auth import IGroup
from silva.pas.base.interfaces import IPASService, IUserConverter

from zeam.form import silva as silvaforms
from zeam.form.ztk.actions import EditAction


class Group(object):
    grok.implements(IGroup)

    def __init__(self, groupid, groupname):
        self.__groupid = groupid
        self.__groupname = groupname

    def groupid(self):
        return self.__groupid

    def groupname(self):
        return self.__groupname

    def allowed_roles(self):
        return roleinfo.ASSIGNABLE_ROLES


class MemberService(SimpleMemberService):
    """Silva Member Service who delagates members search to PAS.
    """
    meta_type = 'Silva Pluggable Auth Service Member Service'
    grok.implements(IPASService)
    grok.name('service_members')
    silvaconf.default_service()
    silvaconf.icon('Membership.png')

    security = ClassSecurityInfo()

    manage_options = (
        {'label':'Settings', 'action':'manage_settings'},
        ) + SimpleMemberService.manage_options

    _display_usernames = False
    _redirect_to_root = False

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
            return None
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
        if pas is None:
            return False
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
        if pas is None:
            return []
        members = root._getOb('Members')

        users = pas.searchUsers(id=search_string, exact_match=False)
        result = []
        for user in users:
            id = user['userid']
            member = members._getOb(id, None)
            if member is None:
                members.manage_addProduct['Silva'].manage_addSimpleMember(id)
                member = members._getOb(id)
                if 'title' in user:
                    member.set_fullname(user['title'])
                if 'email' in user:
                    member.set_email(user['email'])
            result.append(member.__of__(self))

        return result

    security.declareProtected(
        SilvaPermissions.ApproveSilvaContent, 'find_groups')
    def find_groups(self, search_string, location=None):
        """Search for members
        """
        pas = self._get_pas(location=location)
        if pas is None:
            return []
        groups = pas.searchGroups(id=search_string, exact_match=False)
        result = []
        for group in groups:
            result.append(Group(group['groupid'], group['title']))
        return result

    security.declareProtected(
        SilvaPermissions.ApproveSilvaContent, 'use_groups')
    def use_groups(self, location=None):
        pas = self._get_pas(location=location)
        if pas is None:
            return False
        return len(pas.plugins.listPlugins(IGroupEnumerationPlugin)) != 0

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'is_group')
    def is_group(self, groupid, location=None):
        """Check if the given user is a PAS group.
        """
        pas = self._get_pas(location=location)
        if pas is None:
            return False
        # You can retrieve a group from multiple sources
        return (len(pas.searchGroups(exact_match=True, id=groupid)) > 0)

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_group')
    def get_group(self, groupid, location=None):
        pas = self._get_pas(location=location)
        if pas is None:
            return None
        # You can retrieve a group from multiple sources
        groups = pas.searchGroups(exact_match=True, id=groupid)
        if not groups:
            return None
        return Group(groups[0]['groupid'], groups[0]['title'])

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'set_display_usernames')
    def set_display_usernames(self, showed):
        self._display_usernames = showed

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_display_usernames')
    def get_display_usernames(self):
        return self._display_usernames

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'set_redirect_to_root')
    def set_redirect_to_root(self, showed):
        self._redirect_to_root = showed

    security.declareProtected(
        SilvaPermissions.AccessContentsInformation, 'get_redirect_to_root')
    def get_redirect_to_root(self):
        return self._redirect_to_root

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
        if came_from is not None and not self._redirect_to_root:
            exit_url = came_from
        else:
            exit_url = root.absolute_url()

        exit_url += '?' + urllib.urlencode(
            {'login_status': u"You have been logged out."})
        REQUEST.RESPONSE.redirect(exit_url)


InitializeClass(MemberService)


class LoginPage(silvaviews.Page):
    grok.name('silva_login_form.html')

    message = None
    action = None

    def update(self):
        if self.action is None:
            raise BadRequest()
        # Due how PAS monkey patch Zope, we need to do this by hand here.
        headers = queryMultiAdapter(
            (self.request, Exception()),
            IHTTPResponseHeaders)
        if headers is not None:
            headers()


class ISettingsFields(Interface):
    _display_usernames = schema.Bool(title=u'Display user names',
        description=u'Display user names instead of login names in tab access')
    _redirect_to_root = schema.Bool(title=u'Logout redirect to root',
        description=u"Always redirect to root after logout.")


class MemberServiceForm(silvaforms.ZMIForm):
    grok.context(MemberService)
    grok.name('manage_settings')

    ignoreContent = False

    label = u'Manage Member service'
    description = (u'Configure various settings related to user '
                   u'sessions and permissions.')
    fields = silvaforms.Fields(ISettingsFields)
    actions = silvaforms.Actions(EditAction('Save changes'))
