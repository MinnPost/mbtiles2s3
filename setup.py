#!/usr/bin/env python

import sys
from setuptools import setup


# Arg parse is only newly in the standard library
install_requires = [
  'boto >= 2.27.0',
  'progressbar >= 2.2',
  'eventlet >= 0.14.0'
]
if sys.version_info < (2, 7):
  install_requires.append('argparse >= 1.2.1')



setup(
  name = 'mbtiles2s3',
  version = '0.1.0',
  author = 'Alan Palazzolo (MinnPost)',
  author_email = 'apalazzolo@minnpost.com',
  packages = ['mbtiles2s3'],
  scripts = ['bin/mbtiles2s3'],
  url = 'https://github.com/MinnPost/mbtiles2s3',
  license = 'MIT',
  description = 'A command line utility to export an MBTiles file to S3.',
  long_description = open('README.md').read(),
  install_requires = install_requires,
)
