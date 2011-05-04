# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$
from five import grok

from silva.core import conf as silvaconf
from silva.core.smi.userinfo import SimpleUserInfoFieldsFactory
from silva.pas.base.interfaces import (IMemberFactory, IFormFieldFactory,
                                       IPASMember)
from Products.Silva.SimpleMembership import SimpleMember
from zeam.form import silva as silvaforms
from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService

class PASMember(SimpleMember):
    """PAS member get's it's attributes from the PAS user objects"""

    silvaconf.factory('manage_addPASMember')
    silvaconf.icon('member.png')
    grok.implements(IPASMember)
    meta_type = "Silva PAS Member"
    
    def __init__(self, id):
        super(PASMember, self).__init__(id)
        self._email = "ldap"
        
    def email(self):
        """email from pas"""
        pas = getattr(self, 'acl_users')
        if not IPluggableAuthService.providedBy(pas):
            raise RuntimeError, "Expect to be used with a PAS acl user"
        user = pas.getUser(self.userid())
        user.getProperty('first_name')
        # also listPropertysheets() and propertyIds()
        return 'blah'
    
    def fullname(self):
        """fullname from pas"""
        
    def set_fullname(self, fullname):
        raise NotImplemented
    
    def set_email(self):
        raise NotImplemented


def manage_addPASMember(self, id, REQUEST=None):
    """add a PAS member"""
    user = PASMember(id)
    self._setObject(id, user)
    user = getattr(self, id)
    user.manage_addLocalRoles(id, ['ChiefEditor'])
    return ''


class PASMemberFactory(grok.Adapter):
    grok.implements(IMemberFactory)
    grok.context(IPluggableAuthService)
    
    def create(self, memberfolder, userid):
        member = manage_addPASMember(memberfolder, userid)
        return getattr(memberfolder, userid)

class PASUserInfoFieldsFactory(SimpleUserInfoFieldsFactory):
    """factory for returning the silvaforms.Fields schema for PASMembers.
    PAS schema is the SimpleUserInfo schema, but with most fields disabled
    (since they're sourced from PAS and readonly.
    XXX it seems like PAS does allow for non-reaonly attributes, so we may
        want to look in to improving this factory, setting only those
        attributes which are actually readonly in pas as readonly in the form
    """
    grok.context(IPASMember)
    
    def get_fields(self):
        fields = super(PASUserInfoFieldsFactory, self).get_fields()
        fields['fullname'].mode = silvaforms.DISPLAY
        fields['email'].mode = silvaforms.DISPLAY
        #language and avatar ARE STILL editable
        return fields

