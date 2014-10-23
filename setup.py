#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="fs-utilities",
    version="0.0.1",
    author="FineReport Inc.",
    description=("A simple package providing lightweight tools managing files "
                 "from FineReport platform"),
    license="MIT",
    keywords="FineReport platform utilities",
    url="https://github.com/FineDevelop/fs-utilities",
    packages=["fs-utilities",
              "fs-utilities.transfer"],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities",
    ],
    zip_safe=False,
)
