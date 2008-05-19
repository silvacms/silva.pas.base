Copyright (c) 2008, Infrae. All rights reserved.
See also LICENSE.txt

Silva PAS Support
-----------------

This package provides a new service for PAS integration in
Silva. Installing it will also create a new PAS acl_user for the Silva
Root, pre-configured to add users in it.

This extension require at least Silva 2.0.7 or higher.

Installation
------------

If you installed Silva using buildout, by getting one from the `Infrae
SVN`_ repository, or creating one using `Paster`_, you should edit your
buildout configuration file ``buildout.cfg`` to add or edit the
following section::

  [instance]

  eggs = ... 
        silva.pas.base

  zcml = ...
        silva.pas.base

If the section ``instance`` wasn't already in the configuration file,
pay attention to re-copy values for ``eggs`` and ``zcml`` from the
profile you use.

After you can restart buildout::

  ./bin/buildout


If you don't use buildout, you can install this extension using
``easy_install``, and after create a file called
``silva.pas.base-configure.zcml`` in the
``/path/to/instance/etc/package-includes`` directory.  This file will
responsible to load the extension and should only contain this::

       <include package="silva.pas.base" />



.. _Infrae SVN: https://svn.infrae.com/buildout/silva/
.. _Paster: https://svn.infrae.com/buildout/silva/INSTALL.txt
