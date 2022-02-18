#!/usr/bin/env python
# -*- coding: utf-8 -*-


DEV_IP = '164.70.84.254'

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

# メニュー系CSV
MENU_CSV = {'Web': None, 'Fold': None, 'PwBank': None, 'PwWeb': None}

# EAパラメータのファイルパス(Googleドライブ)
PRM_PATH = 'FX/Presets/'

# アイコン
ICON_FILE = '/item/img/logo.ico'

# ネットワーク
import platform
pf = platform.system()
PC = 'Win' if 'Windows' == pf else 'Mac' if 'Darwin' == pf else ''
