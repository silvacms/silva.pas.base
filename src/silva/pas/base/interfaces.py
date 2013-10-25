# -*- coding: utf-8 -*-
# Copyright (c) 2008-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from silva.core.interfaces import ISilvaConfigurableService
from silva.core.services.interfaces import IMemberService, IGroupService
from zope.interface import Interface


class IPASService(IMemberService, IGroupService, ISilvaConfigurableService):
    """PAS Service Membership.
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
