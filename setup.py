#!/usr/bin/env python
import os
from distutils.core import setup

from hydrate_spf import VERSION

# I really prefer Markdown to reStructuredText.  PyPi does not.  This allows me
# to have things how I'd like, but not throw complaints when people are trying
# to install the package and they don't have pypandoc or the README in the
# right place.
try:
   import pypandoc
   description = pypandoc.convert('README.md', 'rst')
except (IOError, OSError, ImportError):
   description = ''
try:
   license = open('LICENSE').read()
except IOError:
   license = 'zlib'

setup(
   name = 'hydrate-spf',
   version = VERSION,
   author = 'James Pearson',
   author_email = 'james@ifixit.com',
   packages = ['hydrate_spf'],
   scripts = ['bin/hydrate-spf'],
   url = 'https://github.com/iFixit/hydrate-spf',
   license = license,
   description = 'A tool to convert an SPF record with nested lookups into a flat list of IPs.',
   long_description = description,
   install_requires = [
      'docopt >= 0.6, < 0.7',
      'ipaddr >= 2.1.11, < 2.2',
      'pydns >= 2.3.6, < 2.4',
      'pyspf >= 2.0.9, < 2.1',
   ],
)

