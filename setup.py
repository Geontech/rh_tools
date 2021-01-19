#!/usr/bin/env python
from setuptools import setup, find_packages
name = "Redhawk Tools"
version = "0.2"
release = "0.2"
author = "Keith Chow"

setup(
    name = name,
    version = version,
    author = author,
    author_email = "kchow@geontech.com",
    description = "Tools to help develop and analyze Redhawk development",
    packages = find_packages(),
    install_requires = ["numpy", "matplotlib", "pyyaml", "scipy",
        "pytest-runner"],
        # "sphinxcontrib.napoleon"],
    tests_require=["pytest"],
    command_options = {
        "build_sphinx" : {
            "project": ("setup.py", name),
            "version": ("setup.py", version),
            "release": ("setup.py", release),
            "source_dir": ("setup.py", "docs/source"),
        }
    }
)