from setuptools import setup, find_packages

version = '0.1'

setup(name='silva.pas.base',
      version=version,
      description="Base PAS support for Silva",
      long_description=open("README.txt").read(),
      classifiers=[
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ], 
      keywords='pas silva',
      author='Sylvain Viollon',
      author_email='info@infrae.com',
      url='https://svn.infrae.com/silva.pas.base/trunk',
      license='ZPL 2.1',
      packages=find_packages(exclude=['ez_setup',]),
      namespace_packages=['silva', 'silva.pas'],
      include_package_data=True,
      zip_safe=False,
      install_requires=["Products.PluggableAuthService >= 1.5.0",
                        "Products.GenericSetup >= 1.3.0, < 1.4.0",
                        "setuptools"],
      )


