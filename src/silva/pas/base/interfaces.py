# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import Interface
from silva.core.services.interfaces import IMemberService, IGroupService
from silva.core.interfaces.auth import IEditableMember

class IPASService(IMemberService, IGroupService):
    """Mark PAS Service Membership.
    """

# BBB
IPASMemberService = IPASService
from silva.core.services.interfaces import ISecretService


class IUserConverter(Interface):
    """Some User can have userid incompatible with Silva SimpleMember.

    This utility can be used to convert them into a compatible one.
    """

    def match(userid):
        """Return true if this userid can be processed by this utility.
        """

    def convert(userid):
        """Return the converted userid.
        """

class IMemberFactory(Interface):
    """Factory used to create a member for a specific type of user.
       Member factories should have the name of the PAS plugin they're
       supporing.
    """
    
    def create(self, userid):
        """Create a Member object for the supplied userid"""
        

class IFormFieldFactory(Interface):
    """Registered on a Silva Member interface (e.g. ISimpleMember),
       to create the silvaforms.Fields object for that type of member"""
    def get_fields():
        """return a silvaforms.Fields object for the user info schema 
           for a type of Silva Member"""
        
class ILDAPMember(IEditableMember):
    """an LDAPMember is an IEditableMember, but MOST of the schema is readonly
    """
