#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ネットワーク
import platform
pf = platform.system()
PC = 'Win' if 'Windows' == pf else 'Mac' if 'Darwin' == pf else ''

MAIN_BGCOLOR = '#AAFFAA'

# Path
from const import path
CURRENT_PATH = path.CURRENT_PATH
GDRIVE_PATH = path.GDRIVE_PATH
TEMP_PATH = path.TEMP_PATH

# URL
from const import url
