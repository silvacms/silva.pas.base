==============
silva.pas.base
==============

This package provides a new service for `PluggableAuthService`_ (PAS)
integration in `Silva`_. Installing it will also create a new PAS
*acl_user* for the Silva Root, pre-configured to add users in it.

In a Silva instance, you cannot mix PAS *acl_user* and regular Zope 2
one.

This extension require at least `Silva`_ 3.0 or higher. For previous
release of Silva, please use previous versions of ``silva.pas.base``.

In `Silva`_ 3.0, it is installed by default.


Code repository
===============

You can find the code of this extension in Git:
https://github.com/silvacms/silva.pas.base

.. _Silva: http://silvacms.org
.. _PluggableAuthService: https://pypi.python.org/pypi/Products.PluggableAuthService
