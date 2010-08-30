# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from zope import interface, schema, component
from zope.cachedescriptors.property import CachedProperty

from silva.core.services.interfaces import IMemberService
from silva.core.cache.store import SessionStore
from silva.core.smi.interfaces import IAccessTab
from silva.core.smi.access import AccessTab
from silva.core.smi import smi as silvasmi
from silva.core.interfaces import ISilvaObject
from silva.translations import translate as _
from zeam.form import silva as silvaforms
from zeam.form.silva.interfaces import IRESTCloseOnSuccessAction


GROUP_STORE_KEY = 'lookup group'

class LookupGroupButton(silvasmi.SMIMiddleGroundRemoteButton):
    grok.view(IAccessTab)
    grok.order(0)

    label = _(u"lookup groups")
    description = _(u"look for groups to assign roles: alt-l")
    action = 'smi-lookupgroup'
    accesskey = u'l'


class ILookupGroupSchema(interface.Interface):

    group = schema.TextLine(
        title=_(u"group name"),
        description=_(u"group name or part of the group name to lookup"),
        required=True)


class LookupGroupAction(silvaforms.Action):
    grok.implements(IRESTCloseOnSuccessAction)

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

        service = component.getUtility(IMemberService)

        store = SessionStore(form.request)
        groups = set()
        for group in service.find_groups(groupname, location=form.context):
            groups.add(group.groupid())
        if groups:
            groups = store.get(GROUP_STORE_KEY, set()).union(groups)
            store.set(GROUP_STORE_KEY, groups)
            form.send_message(
                _(u"Found ${count} groups: ${groups}",
                  mapping={'count': len(groups),
                           'groups': u', '.join(groups)}),
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

    label = _(u'manage group roles')
    description = _(u"find, add and remove roles to groups")


class IGroup(interface.Interface):
    groupname = schema.TextLine(title=u"group name")


class LookupGroupResultForm(silvaforms.SMISubForm):
    """Form to give/revoke access to users.
    """
    grok.context(ISilvaObject)
    grok.order(10)
    grok.view(GroupRole)

    label = _(u"group lookup results")
    ignoreContent = False
    ignoreRequest = True
    mode = silvaforms.DISPLAY
    # fields = silvaforms.Fields(IGrantRole)
    # fields['role'].mode = silvaforms.INPUT
    # fields['role'].ignoreRequest = False
    # fields['role'].ignoreContent = True
    tableFields = silvaforms.Fields(IGroup)
    tableActions = silvaforms.TableActions()

    @CachedProperty
    def store(self):
        return SessionStore(self.request)

    def getGroupIds(self):
        return self.store.get(GROUP_STORE_KEY, set())

    def available(self):
        return len(self.getGroupIds()) != 0

    def getItems(self):
        return []
        group_ids = self.getGroupIds()
        return map(operator.itemgetter(1), authorizations)

    @silvaforms.action(
        _(u"clear result"),
        description=_(u"clear group lookup results"))
    def clear(self):
        self.store.set(GROUP_STORE_KEY, set())
