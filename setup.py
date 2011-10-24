# Copyright (c) 2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from setuptools import setup, find_packages
import os

version = '1.6.2dev'

tests_require = [
    'Products.Silva [test]',
    ]

setup(name='silva.pas.base',
      version=version,
      description="Base PluggableAuthService support for Silva",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        ],
      keywords='pas silva',
      author='Sylvain Viollon',
      author_email='info@infrae.com',
      url='https://svn.infrae.com/silva.pas.base/trunk',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.pas'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "Products.GenericSetup > 1.5.0",
        "Products.PluggableAuthService >= 1.7.0",
        "Products.Silva",
        "five.grok",
        "megrok.chameleon",
        "setuptools",
        "silva.core.cache",
        "silva.core.conf",
        "silva.core.interfaces",
        "silva.core.layout",
        "silva.core.services",
        "silva.core.smi",
        "silva.core.views",
        "zope.component",
        "zope.datetime",
        "zope.schema",
        "zope.session",
        "zope.interface",
        "zope.publisher",
        ],
      entry_points = """
      [zodbupdate]
      renames = silva.pas.base:CLASS_CHANGES
      """,
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      )
