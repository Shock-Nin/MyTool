#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Macアプリ化コマンド
  python3 -m mytool_app.py py2app
"""
import os
from const import cst
from setuptools import setup, find_packages

APP = ['mytool.py']
DATA_FILES = [os.getcwd() + cst.ICON_FILE]

OPTIONS = {'argv_emulation': True,
           'iconfile': DATA_FILES[0],
           'plist': {
            'CFBundleName': 'mytool',
            'CFBundleDisplayName': 'mytool',
            'PyRuntimeLocations': [
                '@executable_path/../Frameworks/libpython3.9.dylib',
                '/opt/anaconda3/lib/libpython3.9.dylib'
               ]
           }}

setup(
    app=APP,
    data_files=DATA_FILES,
    packages=find_packages(),
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)
