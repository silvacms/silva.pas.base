silva.pas.base
**************

This package provides a new service for PluggableAuthService (PAS)
integration in `Silva`. Installing it will also create a new PAS
*acl_user* for the Silva Root, pre-configured to add users in it.

In a Silva instance, you cannot mix PAS *acl_user* and regular Zope 2
one.

This extension require at least `Silva`_ 3.0 or higher. For previous
release of Silva, please use previous versions of ``silva.pas.base``.


Code repository
===============

You can find the code of this extension in Mercurial:
https://hg.infrae.com/silva.pas.base/.

.. _Silva: http://silvacms.org
