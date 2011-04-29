
from five import grok

from Products.LDAPMultiPlugins.LDAPPluginBase import ILDAPMultiPlugin
from silva.core import conf as silvaconf
from silva.core.smi.userinfo import SimpleUserInfoFieldsFactory
from silva.pas.base.interfaces import (IMemberFactory, IFormFieldFactory,
                                       ILDAPMember)
from Products.Silva.SimpleMembership import SimpleMember
from zeam.form import silva as silvaforms
from Products.PluggableAuthService.interfaces.authservice import \
    IPluggableAuthService

class LDAPMember(SimpleMember):
    """ldap member get's it's attributes from LDAP, I.E. the 
       pas LDAPMultiPlugin"""

    silvaconf.factory('manage_addLDAPMember')
    silvaconf.icon('member.png')
    grok.implements(ILDAPMember)
    meta_type = "Silva LDAP Member"
    
    def __init__(self, id):
        super(LDAPMember, self).__init__(id)
        self._email = "ldap"
        
    def email(self):
        """email from ldap"""
        pas = getattr(self, 'acl_users')
        if not IPluggableAuthService.providedBy(pas):
            raise RuntimeError, "Expect to be used with a PAS acl user"
        user = pas.getUser(self.userid())
        user.getPropertysheet('bethelad').getProperty('first_name')
        # also listPropertysheets() and proeprtyIds()
        return 'blah'
        
    
    def fullname(self):
        """fullname from ldap"""
        
    def set_fullname(self, fullname):
        raise NotImplemented
    
    def set_email(self):
        raise NotImplemented


def manage_addLDAPMember(self, id, REQUEST=None):
    """add an LDAP member"""
    user = LDAPMember(id)
    self._setObject(id, user)
    user = getattr(self, id)
    user.manage_addLocalRoles(id, ['ChiefEditor'])
    return ''


class LDAPMemberFactory(grok.Adapter):
    grok.implements(IMemberFactory)
    grok.context(ILDAPMultiPlugin)
    
    def create(self, memberfolder, userid):
        member = manage_addLDAPMember(memberfolder, userid)
        return getattr(memberfolder, userid)

class LDAPUserInfoFieldsFactory(SimpleUserInfoFieldsFactory):
    """factory for returning the silvaforms.Fields schema for LDAPMembers.
    LDAP schema is the SimpleUserInfo schema, but with most fields disabled
    (since they're sourced from LDAP and readonly."""
    grok.implements(IFormFieldFactory)
    grok.context(ILDAPMember)
    
    def get_fields(self):
        fields = super(LDAPUserInfoFieldsFactory, self).get_fields()
        fields['fullname'].mode = silvaforms.DISPLAY
        fields['email'].mode = silvaforms.DISPLAY
        #language and avatar ARE STILL editable
        return fields

