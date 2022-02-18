#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import path
from const import url

# 英単語再生、監視待機回数(3秒単位)
ENG1MIN_MONITOR = 20

# EA並び順
EA_PATHS = {
    'AnomalyGoToBe': ['Other'],
    'AnomalyShocknin': ['Main', 'Unit-']
}
CURRNCYS_EA = ['EUR', 'GBP', 'AUD', 'NZD', 'JPY', 'CHF', 'CAD', 'GOLD']
CURRNCYS_365 = ['JPY', 'EUR', 'GBP', 'AUD', 'CHF', 'CAD', 'NZD',
                'ZAR', 'TRY', 'NOK', 'HKD', 'SEK', 'MXN', 'PLN']
EA_DATA_NAMES = ['EA個別成績', 'EA統合成績', 'EA統合年率']

# メイン画面色
MAIN_BGCOLOR = '#FFCCFF' if 'Win' == path.PC else '#AAFFAA'
MAIN_ACT_COLOR = ['#FFFF77', '#000000']

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
MENU_CSV = path.MENU_CSV
ICON_FILE = path.ICON_FILE

# URL
BLOG_URL = url.BLOG_URL
