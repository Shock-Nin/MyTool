#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
python setup.py py2app
"""
import os
from const import cst
from setuptools import setup

APP = ['mytool.py']
DATA_FILES = [cst.ICON_FILE]

OPTIONS = {'argv_emulation': True,
           'iconfile': cst.ICON_FILE,
           'plist': {
            'CFBundleName': 'MyTool',
            'CFBundleDisplayName': 'MyTool',
            'PyRuntimeLocations': [
                '@executable_path/../Frameworks/libpython3.9.dylib',
                '/opt/anaconda3/lib/libpython3.9.dylib'
               ]
           }}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)
