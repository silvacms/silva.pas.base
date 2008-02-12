Copyright (c) 2007, Infrae. All rights reserved.
See also LICENSE.txt

Silva PAS Support
-----------------

This package includes the following:

* installation of Radius authentication support for Silva.

* a special membership extension for Silva designed to work with this
  Radius integration. 

Normally Silva offers the following workflow for assigning local roles
to users. First, users are placed on the user clipboard in the user
lookup screen (access tab -> lookup). The idea is that this screen is
connected to some user directory or database and that users are looked
up in there. The lookup screen cannot be made to work with Radius, as
Radius only takes care of authentication, and does not include a user
directory (unlike LDAP which does both).

In order to still have the ability to place users on the user
clipboard, the membership extension has been configured to enable a
new user interface (introduced in Silva 2.1). Using this UI it is
possible to directly add users to the clipboard by username. Once they
are on the clipboard, they can be assigned a role in the access tab,
or added to a group.

See INSTALL.txt for installation information.
