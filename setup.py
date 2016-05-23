#!/usr/bin/env python3

import sys

# Try using setuptools first, if it's installed
from setuptools import setup, find_packages

# Need to add all dependencies to setup as we go!
setup(name='PyCmdMessenger',
      version='0.1',
      description='Python interface for CmdMessenger arduino serial communication library',
      author='Michael J. Harms',
      url='https://github.com/harmsm/PyCmdMessenger',
      packages=find_packages(),
      zip_safe=False,
      install_requires=["pyserial"])

