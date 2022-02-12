#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ネットワーク
import platform
pf = platform.system()
PC = 'Win' if 'Windows' == pf else 'Mac' if 'Darwin' == pf else ''

MAIN_BGCOLOR = '#FFAAFF' if 'Win' == PC else '#AAFFAA'

# Path
from const import path
CURRENT_PATH = path.CURRENT_PATH
GDRIVE_PATH = path.GDRIVE_PATH
TEMP_PATH = path.TEMP_PATH
MT4_DEV = path.MT4_DEV
DATA_PATH = path.DATA_PATH
TEST_UNIT = path.TEST_UNIT
TEST_OUT_PATH = path.TEST_OUT_PATH
PRM_PATH = path.PRM_PATH
DEV_IP = path.DEV_IP

# URL
from const import url
BLOG_URL = url.BLOG_URL
