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
from Products.PluggableAuthService.interfaces.plugins import \
    IPropertiesPlugin

marker = object()

class PASMember(SimpleMember):
    """PAS member get's it's attributes from the PAS user objects
    
       If property doesn't exist in PAS, pull it from
       SimpleMember.  I can't think of a better, automated way to
       allow empty pas properties to be empty, falling back to Member
       properties.  (PAS properties are fine for ldap or radius, but
       local zope users in a pas don't have these properties, and they
       still need to be set-able.
    """

    silvaconf.factory('manage_addPASMember')
    silvaconf.icon('member.png')
    grok.implements(IPASMember)
    meta_type = "Silva PAS Member"
    
    def __init__(self, id):
        super(PASMember, self).__init__(id)
        
    def __get_property__(self, prop, empty=marker):
        """Get a property from the PAS user.

           PAS users are PropertyManagers, so getProperty _should_ work
           to retrieve properties from the IPropertiesPlugins, but it does
           not.  Instead, you need to retrieve the appropriate propertysheet
           and get the property from the sheet directly.
        """
        pas = getattr(self, 'acl_users')
        if not IPluggableAuthService.providedBy(pas):
            raise RuntimeError, "Expect to be used with a PAS acl user"
        user = pas.getUser(self.userid())
        #listPlugins returns a 2-tuple of (plugin id, plugin obj)
        plugins = pas.plugins.listPlugins(IPropertiesPlugin)
        for (pid,plug) in plugins:
            try:
                return user.getPropertysheet(pid).getProperty(prop)
            except KeyError:
                pass
        return marker
        
    def email(self):
        """email from pas."""
        prop = self.__get_property__('email')
        if prop is marker: #property not in PAS
            return super(PASMember, self).email()
        return prop
    
    def fullname(self):
        """fullname from pas"""
        prop = self.__get_property__('fullname')
        if prop is marker: #property not in PAS
            return super(PASMember, self).fullname()
        return prop
        
    def set_fullname(self, fullname):
        """only allow setting fullname if there is no fullname pas property"""
        if self.__get_property__('fullname') is not marker:
            raise NotImplemented
        return super(PASMember, self).set_fullname(fullname)
    
    def set_email(self, email):
        """only allow setting fullname if there is no fullname pas property"""
        if self.__get_property__('email') is not marker:
            raise NotImplemented
        return super(PASMember, self).set_email(email)
    
    def can_edit_property(self, prop):
        """returns True if the property is editable.  This is only possible
           if the property for the user does not exist in PAS"""
        return self.__get_property__(prop) is marker


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
    (since they're sourced from PAS and readonly.  If the property is editable
    (i.e. it is NOT in PAS), leave it editable.
    XXX it seems like PAS does allow for non-reaonly attributes, so we may
        want to look in to improving this factory, setting only those
        attributes which are actually readonly in pas as readonly in the form
    """
    grok.context(IPASMember)
    
    def get_fields(self):
        fields = super(PASUserInfoFieldsFactory, self).get_fields()
        #these fields are editable if they do not exist in PAS
        if not self.context.can_edit_property('fullname'):
            fields['fullname'].mode = silvaforms.DISPLAY
        if not self.context.can_edit_property('email'):
            fields['email'].mode = silvaforms.DISPLAY
        return fields

