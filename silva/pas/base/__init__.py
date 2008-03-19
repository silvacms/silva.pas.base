# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import install
import Membership

from Products.Silva.ExtensionRegistry import extensionRegistry

def initialize(context):
    extensionRegistry.register(
        'silva.pas.base', 'Silva Pluggable Auth Service Support', context, [],
        install, depends_on='Silva')
    
    context.registerClass(
        Membership.MemberService,
        constructors = (Membership.manage_addMemberServiceForm,
                        Membership.manage_addMemberService),
        )

