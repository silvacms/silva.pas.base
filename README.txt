silva.pas.base
**************

This package provides a new service for PluggableAuthService (PAS)
integration in Silva. Installing it will also create a new PAS
*acl_user* for the Silva Root, pre-configured to add users in it.

In a Silva instance, you cannot mix PAS *acl_user* and regular Zope 2
one.

This extension require at least `Silva`_ 2.3 or higher. For previous
release of Silva, please use previous versions of ``silva.pas.base``.

Installation
============

If you installed Silva using buildout, by getting one from the `Infrae
SVN`_ repository, or creating one using `Paster`_, you should edit your
buildout configuration file ``buildout.cfg`` to add or edit the
following section::

  [instance]

  eggs += 
        silva.pas.base

  zcml += 
        silva.pas.base

If the section ``instance`` wasn't already in the configuration file,
pay attention to re-copy values for ``eggs`` and ``zcml`` from the
profile you use.

After you can restart buildout::

  $ ./bin/buildout


Latest version
==============

The latest version is available in a `Subversion repository
<https://svn.infrae.com/silva.pas.base/trunk#egg=silva.pas.base-dev>`_.


.. _Infrae SVN: https://svn.infrae.com/buildout/silva/
.. _Paster: https://svn.infrae.com/buildout/silva/INSTALL.txt
.. _Silva: http://infrae.com/products/silva
