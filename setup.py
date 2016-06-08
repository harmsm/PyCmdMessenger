#!/usr/bin/env python3

import sys

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

if not sys.version_info[0] == 3:
    sys.exit("Sorry, Python 3 is required")

# Need to add all dependencies to setup as we go!
setup(name='PyCmdMessenger',
      packages=['PyCmdMessenger'],
      version='0.2.3',
      description='Python interface for CmdMessenger arduino serial communication library',
      author='Michael J. Harms',
      author_email='harmsm@gmail.com',
      url='https://github.com/harmsm/PyCmdMessenger',
      download_url='https://github.com/harmsm/PyCmdMessenger/tarball/0.2.3',
      zip_safe=False,
      install_requires=["pyserial"],
      classifiers=['Programming Language :: Python'])

