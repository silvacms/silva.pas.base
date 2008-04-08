# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import Interface
from Products.Silva.interfaces import IMemberService

class IPASMemberService(IMemberService):
    """Mark PAS Service Membership.
    """


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




