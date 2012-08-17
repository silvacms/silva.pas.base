# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import operator

from five import grok
from zope import schema, component
from zope.interface import Interface
from zope.cachedescriptors.property import CachedProperty

from silva.core.cache.store import SessionStore
from silva.core.interfaces import ISilvaObject
from silva.core.interfaces import UnauthorizedRoleAssignement
from silva.core.interfaces.auth import role_vocabulary, IAuthorizationManager
from silva.core.services.interfaces import IGroupService, MemberLookupError
from silva.core.smi.settings.access import Access, IGrantRoleSchema
from silva.core.views.interfaces import IVirtualSite
from silva.translations import translate as _
from silva.ui.rest import UIREST
from zeam.form import silva as silvaforms
from zeam.form.silva.interfaces import (
    IRESTCloseOnSuccessAction, IRESTRefreshAction,
    IRemoverAction, IDefaultAction)

from zExceptions import BadRequest


## Login form in SMI, in a popup

class ILoginFields(Interface):
    name = schema.TextLine(
        title=_(u"Login"),
        required=True)
    password = schema.Password(
        title=_(u"Password"),
        required=True)
    secret = schema.TextLine(
        title=u"Secret",
        required=True)
    origin = schema.TextLine(
        title=u"Origin",
        required=True)


def next_action_url(action):

    def action_url(form):
        url = IVirtualSite(form.request).get_root_url()
        return '/'.join((url, '++rest++' + action))

    return action_url


class LoginPage(silvaforms.PopupForm):
    grok.context(Interface)
    grok.name('xml_login_form.html')
    # You can view this login page as it is not possible to call with
    # a different submit URL. This makes validation works.
    grok.require('zope2.Public')

    action = None
    message = None
    novalidation = True
    prefix = '__ac'
    label = _(u"Restricted access")
    description = _(u"You need to login with new credentials in order to continue.")
    fields = silvaforms.Fields(ILoginFields)
    fields['secret'].mode = silvaforms.HIDDEN
    fields['origin'].mode = silvaforms.HIDDEN
    fields['origin'].ignoreRequest = True
    fields['origin'].defaultValue = next_action_url('silva.pas.base.loggedin')
    actions = silvaforms.Actions(
        silvaforms.CancelAction())

    @silvaforms.action(
        _(u"Login"),
        implements=(IDefaultAction, IRESTCloseOnSuccessAction))
    def login(self):
        # Empty action to create a submit button. form_url is changed
        # below, the form will not be submitted here.
        return silvaforms.SUCCESS

    def updateForm(self):
        # The cookie plugin must set action and status on the form. If
        # this is not set, someone is trying to hack the matrice.
        if self.action is None:
            raise BadRequest()
        if self.message:
            self.send_message(self.message, type="error")
        # Change the form url to the real login submit
        result = super(LoginPage, self).updateForm()
        result['content']['submit_url'] = self.action
        return result


class LoggedInMessage(UIREST):
    grok.name('silva.pas.base.loggedin')

    def GET(self):
        """Return a message after the user successfully logged in.
        """
        return self.json_response({
                'content': {
                    'ifaces': ['message'],
                    'title': self.translate(_(u'Logged in')),
                    'message': self.translate(_(u'You are now authenticated.'))}})

## Group support

GROUP_STORE_KEY = 'lookup group'


class LookupGroupPopupAction(silvaforms.PopupAction):
    title = _(u"Lookup groups...")
    description = _(u"Search for groups to assign roles")
    action = 'smi-lookupgroup'
    accesskey = u'g'


class ILookupGroupSchema(Interface):
    """Lookup a group
    """
    group = schema.TextLine(
        title=_(u"Group name"),
        description=_(u"Group name or part of a group name to lookup"),
        default=u'',
        required=False)


class LookupGroupAction(silvaforms.Action):
    grok.implements(IRESTCloseOnSuccessAction, IRESTRefreshAction)
    refresh = 'form.grouprole.lookupgroupresultform'

    title = _(u"Lookup group")
    description=_(u"Search for groups in order to assign them roles")

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        groupname = data.getDefault('group').strip()

        service = component.getUtility(IGroupService)
        groups = set()
        new_groups = set()
        try:
            for group in service.find_groups(groupname, location=form.context):
                groupid = group.groupid()
                groups.add(groupid)
                new_groups.add(groupid)
        except MemberLookupError as error:
            form.send_message(error.args[0], type="error")
            return silvaforms.FAILURE

        store = SessionStore(form.request)
        if new_groups:
            groups = store.get(GROUP_STORE_KEY, set()).union(groups)
            store.set(GROUP_STORE_KEY, groups)
            form.send_message(
                _(u"Found ${count} groups: ${groups}.",
                  mapping={'count': len(new_groups),
                           'groups': u', '.join(new_groups)}),
                type="feedback")
        else:
            form.send_message(
                _(u"No matching groups found."),
                type="error")
            return silvaforms.FAILURE
        return silvaforms.SUCCESS


class LookupGroupForm(silvaforms.RESTPopupForm):
    """Form to manage default permission needed to see the current
    content.
    """
    grok.context(ISilvaObject)
    grok.name('smi-lookupgroup')

    label = _(u"Lookup groups")
    description = _(u"Search for groups to assign them roles. "
                    u"Leave the field empty to get all groups "
                    u"(could be a long list).")
    fields = silvaforms.Fields(ILookupGroupSchema)
    actions = silvaforms.Actions(
        LookupGroupAction(),
        silvaforms.CancelAction())


class GroupRole(silvaforms.SMISubFormGroup):
    grok.context(ISilvaObject)
    grok.order(50)
    grok.view(Access)

    def available(self):
        service = component.queryUtility(IGroupService)
        return (service is not None and
                service.use_groups() and
                super(GroupRole, self).available())


class IGroupAuthorization(Interface):

    identifier = schema.TextLine(
        title=_(u"Group name"))
    acquired_role = schema.Choice(
        title=_(u"Role defined above"),
        source=role_vocabulary,
        required=False)
    local_role = schema.Choice(
        title=_(u"Role defined here"),
        source=role_vocabulary,
        required=False)


class GrantAccessAction(silvaforms.Action):

    title = _(u"Grant role")
    description = _(u"Grant the selected role to the selected groups(s)")

    def available(self, form):
        return len(form.lines) != 0

    def __call__(self, form, authorization, line):
        data, errors = form.extractData(form.fields)
        if errors:
            return silvaforms.FAILURE
        role = data['role']
        if not role:
            return form.revoke(authorization, line)
        mapping = {'role': role,
                   'groupname': authorization.identifier}
        try:
            if authorization.grant(role):
                form.send_message(
                    _('Role "${role}" granted to group "${groupname}".',
                      mapping=mapping),
                    type="feedback")
            else:
                form.send_message(
                    _('Group "${groupname}" already has the role "${role}".',
                      mapping=mapping),
                    type="error")
        except UnauthorizedRoleAssignement as error:
            form.send_message(
                _(u'Sorry, you are not allowed to remove the role "${role}" '
                  u'from group "${groupid}": ${reason}.',
                  mapping={'role': error.role,
                           'groupid': error.identifier,
                           'reason': error.reason}),
                type="error")
        return silvaforms.SUCCESS


class RevokeAccessAction(silvaforms.Action):
    grok.implements(IRemoverAction)

    title = _(u"Revoke role")
    description=_(u"Revoke the role of selected group(s)")

    def available(self, form):
        return reduce(
            operator.or_,
            [False] + map(lambda l: l.getContent().local_role is not None,
                          form.lines))

    def __call__(self, form, authorization, line):
        try:
            role = authorization.local_role
            groupname = authorization.identifier
            if authorization.revoke():
                form.send_message(
                    _(u'Removed role "${role}" from group "${groupname}".',
                      mapping={'role': role,
                               'groupname': groupname}),
                    type="feedback")
            else:
                form.send_message(
                    _(u'Group "${groupname}" doesn\'t have any local role.',
                      mapping={'groupname': groupname}),
                    type="error")
        except UnauthorizedRoleAssignement as error:
            form.send_message(
                _(u'Sorry, you are not allowed to remove the role "${role}" '
                  u'from group "${groupid}": ${reason}.',
                  mapping={'role': error.role,
                           'groupid': error.identifier,
                           'reason': error.reason}),
                type="error")
        return silvaforms.SUCCESS


class GroupRoleForm(silvaforms.SMISubTableForm):
    """Form to grant/revoke access to users.
    """
    grok.context(ISilvaObject)
    grok.order(20)
    grok.view(GroupRole)

    label = _(u"Group roles")
    emptyDescription = _(u'No roles have been assigned.')
    ignoreContent = False
    ignoreRequest = True
    mode = silvaforms.DISPLAY
    fields = silvaforms.Fields(IGrantRoleSchema)
    fields['role'].mode = silvaforms.INPUT
    fields['role'].ignoreRequest = False
    fields['role'].ignoreContent = True
    fields['role'].available = lambda form: len(form.lines) != 0
    tableFields = silvaforms.Fields(IGroupAuthorization)
    tableActions = silvaforms.TableActions(
        GrantAccessAction(),
        RevokeAccessAction())

    def getItems(self):
        access = IAuthorizationManager(self.context)
        authorizations = access.get_defined_authorizations().items()
        authorizations.sort(key=operator.itemgetter(0))
        return filter(lambda auth: auth.type == 'group',
                      map(operator.itemgetter(1), authorizations))


class LookupGroupResultForm(GroupRoleForm):
    """Form to grant/revoke access to users.
    """
    grok.order(10)

    label = _(u"Group clipboard")
    emptyDescription = _(u"Search for groups to assign them roles.")
    actions = silvaforms.Actions()
    tableActions = silvaforms.TableActions(GrantAccessAction())

    @CachedProperty
    def store(self):
        return SessionStore(self.request)

    def getItems(self):
        group_ids = self.store.get(GROUP_STORE_KEY, set())
        if group_ids:
            access = IAuthorizationManager(self.context)
            authorizations = access.get_authorizations(group_ids).items()
            authorizations.sort(key=operator.itemgetter(0))
            return filter(lambda auth: auth.type == 'group',
                          map(operator.itemgetter(1), authorizations))
        return []

    @silvaforms.action(
        _(u"Clear clipboard"),
        description=_(u"Remove the group lookup results"),
        available=lambda form: len(form.lines) != 0,
        implements=IRemoverAction)
    def clear(self):
        self.store.set(GROUP_STORE_KEY, set())

    actions += LookupGroupPopupAction()
