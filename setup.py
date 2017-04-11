#!/usr/bin/env python3

from setuptools import setup, find_packages

import os
import sys

VERSION = '0.9.3'

_long_desc = "Macumba"
with open('README.md', 'r') as fp:
    _long_desc = fp.read()

REQUIREMENTS = [
    "requests",
    "ws4py",
    "PyYAML"
]

TEST_REQUIREMENTS = list(REQUIREMENTS)
TEST_REQUIREMENTS.extend(["mock", "nose"])

if sys.argv[-1] == 'clean':
    print("Cleaning up ...")
    os.system('rm -rf macumba.egg-info build dist')
    sys.exit()

if sys.argv[-1] == 'version':
    print(VERSION)
    sys.exit()

setup(name='macumba',
      version=VERSION,
      description="Python 3 bindings for Juju",
      long_description=_long_desc,
      author='Canonical Solutions Engineering',
      author_email='ubuntu-dev@lists.ubuntu.com',
      url='https://github.com/Ubuntu-Solutions-Engineering/macumba',
      license="LGPL-3",
      entry_points={
        "console_scripts": [
            "macumba-shell = macumba.cli:main"
        ]
      },
      install_requires=REQUIREMENTS,
      packages=find_packages(exclude=["test"]))
