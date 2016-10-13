#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

import os, sys

from setuptools import setup, find_packages

setup(
    name='incremental',
    use_incremental=True,
    maintainer='Glyph',
    maintainer_email='glyph@twistedmatrix.com',
    url="https://github.com/hawkowl/incremental",
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    setup_requires=[
        "incremental"
    ],
    install_requires=[
        "twisted>=16.4",
        "incremental",
        "attr",
    ],
    license="MIT",
    zip_safe=False,
    long_description=open('README.rst').read(),
)
