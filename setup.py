##########################################################################
# CAPSUL - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from ez_setup import use_setuptools
use_setuptools()
import os
from setuptools import find_packages, setup
import argparse
import sys

# Select appropriate modules
modules = find_packages()
scripts = ["capsul/qt_apps/capsulview"]
pkgdata = {
"capsul.qt_apps.resources": ["*.ui", "*.png", "*.gif", "*.qrc", "*.txt"],
"capsul.utils.test": ["*.xml"],
"capsul.pipeline.test": ["*.json"]
}
release_info = {}
execfile(os.path.join("capsul", "info.py"), release_info)

# Build the setup
setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    classifiers=release_info["CLASSIFIERS"],
    author=release_info["AUTHOR"],
    author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["VERSION"],
    url=release_info["URL"],
    packages=modules,
    package_data=pkgdata,
    platforms=release_info["PLATFORMS"],
    extras_require=release_info["EXTRA_REQUIRES"],
    install_requires=release_info["REQUIRES"],
    scripts=scripts
)
