# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from zope import interface, schema, component
from zope.cachedescriptors.property import CachedProperty

from silva.core.cache.store import SessionStore
from silva.core.interfaces import ISilvaObject
from silva.core.services.interfaces import IGroupService
from silva.core.smi.access import AccessTab, IGrantRoleSchema
from silva.translations import translate as _
from zeam.form import silva as silvaforms
from zeam.form.silva.interfaces import (
    IRESTCloseOnSuccessAction, IRESTRefreshAction)


GROUP_STORE_KEY = 'lookup group'


class LookupGroupPopupAction(silvaforms.PopupAction):
    title = _(u"lookup groups")
    description = _(u"look for groups to assign roles: alt-g")
    action = 'smi-lookupgroup'
    accesskey = u'g'


class ILookupGroupSchema(interface.Interface):
    """Look for a group
    """
    group = schema.TextLine(
        title=_(u"group name"),
        description=_(u"group name or part of the group name to lookup"),
        required=True)


class LookupGroupAction(silvaforms.Action):
    grok.implements(IRESTCloseOnSuccessAction, IRESTRefreshAction)
    refresh = 'form-grouprole'

    title = _(u"lookup group")
    description=_(u"look for groups in order to assign them roles")

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        groupname = data['group'].strip()
        if len(groupname) < 2:
            form.send_message(
                _(u"Search input is too short. "
                  u"Please supply more characters"),
                type="error")
            return silvaforms.FAILURE

        service = component.getUtility(IGroupService)

        store = SessionStore(form.request)
        groups = set()
        new_groups = set()
        for group in service.find_groups(groupname, location=form.context):
            groupid = group.groupid()
            groups.add(groupid)
            new_groups.add(groupid)
        if new_groups:
            groups = store.get(GROUP_STORE_KEY, set()).union(groups)
            store.set(GROUP_STORE_KEY, groups)
            form.send_message(
                _(u"Found ${count} groups: ${groups}",
                  mapping={'count': len(new_groups),
                           'groups': u', '.join(new_groups)}),
                type="feedback")
        else:
            form.send_message(
                _(u"No matching groups"),
                type="error")
            return silvaforms.FAILURE
        return silvaforms.SUCCESS


class LookupGroupForm(silvaforms.RESTPopupForm):
    """Form to manage default permission needed to see the current
    content.
    """
    grok.context(ISilvaObject)
    grok.name('smi-lookupgroup')

    label = _(u"lookup groups")
    description = _(u"Look for groups to assign them roles.")
    fields = silvaforms.Fields(ILookupGroupSchema)
    actions = silvaforms.Actions(
        LookupGroupAction(),
        silvaforms.CancelAction())


class GroupRole(silvaforms.SMISubFormGroup):
    grok.context(ISilvaObject)
    grok.order(50)
    grok.view(AccessTab)

    def available(self):
        service = component.queryUtility(IGroupService)
        return (service is not None and
                service.use_groups() and
                super(GroupRole, self).available())


class IGroupSchema(interface.Interface):
    groupname = schema.TextLine(title=u"group name")


class GroupRoleForm(silvaforms.SMISubTableForm):
    """Form to give/revoke access to users.
    """
    grok.context(ISilvaObject)
    grok.order(20)
    grok.view(GroupRole)

    label = _(u"group roles")
    ignoreContent = False
    ignoreRequest = True
    mode = silvaforms.DISPLAY
    fields = silvaforms.Fields(IGrantRoleSchema)
    fields['role'].mode = silvaforms.INPUT
    fields['role'].ignoreRequest = False
    fields['role'].ignoreContent = True
    fields['role'].available = lambda form: len(form.lines) != 0
    tableFields = silvaforms.Fields(IGroupSchema)
    tableActions = silvaforms.TableActions()

    def getItems(self):
        return []


class LookupGroupResultForm(GroupRoleForm):
    """Form to give/revoke access to users.
    """
    grok.context(ISilvaObject)
    grok.order(10)
    grok.view(GroupRole)

    label = _(u"group clipboard")
    emptyDescription = _(u"Search for groups to assign them roles")
    actions = silvaforms.Actions(LookupGroupPopupAction())
    tableActions = silvaforms.TableActions()

    @CachedProperty
    def store(self):
        return SessionStore(self.request)

    def getItems(self):
        group_ids = self.store.get(GROUP_STORE_KEY, set())
        if group_ids:
            service = component.getUtility(IGroupService)
            return map(service.get_group, group_ids)
        return [] # map(operator.itemgetter(1), authorizations)

    @silvaforms.action(
        _(u"clear result"),
        description=_(u"clear group lookup results"),
        available=lambda form: len(form.lines) != 0)
    def clear(self):
        self.store.set(GROUP_STORE_KEY, set())
