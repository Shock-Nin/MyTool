#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
IP = requests.get('https://ifconfig.me').text

WEB_IP = '164.70.84.131'
MY_IP = '164.70.84.169'
DEV_IP = '164.70.84.254'
MAC_IP = '133.32.224.211'
IPS = {
    WEB_IP: 'Web',
    MY_IP: 'My',
    DEV_IP: 'DEV',
    MAC_IP: 'Mac',
}

CURRENT_PATH = {
    'Mac': '/Users/dsk_nagaoka/',
    'Win': 'C:/Users/Administrator/',
}
GDRIVE_PATH = {
    'Mac': CURRENT_PATH['Mac'] + 'Google ドライブ/',
    'Win': CURRENT_PATH['Win'] + 'Google ドライブ/',
}
TEMP_PATH = {
    'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/',
    'Win': CURRENT_PATH['Win'] + 'Documents/MyToolTmp/',
}

# 開発MT4のパス
MT4_DEV = {
    'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/',
    'Win': CURRENT_PATH['Win'] + 'Documents/MT4/MT4_DEV/OANDA/',
}

# パラメータ・集計データのCSV・HTML格納フォルダ
DATA_PATH = {
    'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/frame/',
    'Win': 'C:/inetpub/wwwroot/menu/frame/',
}

# EAの単独テスト
TEST_UNIT = {
    'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/Test/',
    'Win': CURRENT_PATH['Win'] + 'Documents/Test/',
}

# テスト集計データの出力先
TEST_OUT_PATH = {
    'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/out_test/',
    'Win': 'C:/inetpub/wwwroot/test/',
}
# テストリンク
TEST_LINK = {
    'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/out_test/',
    'Win': 'http://' + DEV_IP + '/test/',
}

# ReportManagerのパス
RM_EXE = GDRIVE_PATH['Win'] + 'app/ReportManager'

# TickStoryのExeと作成先フォルダ
TICK_HISTORY = [
    'C:/Program Files (x86)/Tickstory/Tickstory.exe',
    CURRENT_PATH['Win'] + 'Documents/MT4/history'
]

# メニュー系CSV
MENU_CSV = {'Web': None, 'Fold': None, 'PwBank': None, 'PwWeb': None, 'Sql': None}

# EAパラメータのファイルパス(Googleドライブ)
PRM_PATH = 'FX/Presets/'

# アイコン
ICON_FILE = '/item/img/logo.ico'

# ネットワーク
import platform
pf = platform.system()
PC = 'Win' if 'Windows' == pf else 'Mac' if 'Darwin' == pf else ''
