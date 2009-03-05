silva.pas.base
**************

This package provides a new service for PluggableAuthService (PAS)
integration in Silva. Installing it will also create a new PAS
*acl_user* for the Silva Root, pre-configured to add users in it.

This extension require at least `Silva`_ 2.1.2 or higher. For previous
release of Silva, please use ``silva.pas.base`` 1.2.

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


If you don't use buildout, you can install this extension using
``easy_install``, and after create a file called
``silva.pas.base-configure.zcml`` in the
``/path/to/instance/etc/package-includes`` directory.  This file will
responsible to load the extension and should only contain this::

  <include package="silva.pas.base" />


Latest version
==============

The latest version is available in a `Subversion repository
<https://svn.infrae.com/silva.pas.base/trunk#egg=silva.pas.base-dev>`_.


.. _Infrae SVN: https://svn.infrae.com/buildout/silva/
.. _Paster: https://svn.infrae.com/buildout/silva/INSTALL.txt
.. _Silva: http://infrae.com/products/silva
