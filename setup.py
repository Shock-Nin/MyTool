#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
python setup.py py2app
"""
from setuptools import setup

APP = ['mytool.py']
DATA_FILES = ['item/img/logo.ico']
OPTIONS = {'argv_emulation': True,
           'plist': {
               'PyRuntimeLocations': [
                '@executable_path/../Frameworks/libpython3.9.dylib',
                '/opt/anaconda3/lib/libpython3.9.dylib'
               ]
           }}
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
