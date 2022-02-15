#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import path
from const import url

# EA並び順
EA_PATHS = {
    'AnomalyGoToBe': ['Other'],
    'AnomalyShocknin': ['Main', 'Unit-']
}
CURRNCYS_EA = ['EUR', 'GBP', 'AUD', 'NZD', 'JPY', 'CHF', 'CAD', 'GOLD']
CURRNCYS_365 = ['JPY', 'EUR', 'GBP', 'AUD', 'CHF', 'CAD', 'NZD',
                'ZAR', 'TRY', 'NOK', 'HKD', 'SEK', 'MXN', 'PLN']

# メイン画面色
MAIN_BGCOLOR = '#FFAAFF' if 'Win' == path.PC else '#AAFFAA'

# Path
PC = path.PC
CURRENT_PATH = path.CURRENT_PATH
GDRIVE_PATH = path.GDRIVE_PATH
TEMP_PATH = path.TEMP_PATH
MT4_DEV = path.MT4_DEV
DATA_PATH = path.DATA_PATH
TEST_UNIT = path.TEST_UNIT
TEST_OUT_PATH = path.TEST_OUT_PATH
PRM_PATH = path.PRM_PATH
TEST_LINK = path.TEST_LINK

# URL
BLOG_URL = url.BLOG_URL
