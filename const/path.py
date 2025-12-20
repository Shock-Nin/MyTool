#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ネットワーク
import socket
import platform

pf = platform.system()
PC = 'Win' if 'Windows' == pf else 'Mac' if 'Darwin' == pf else ''
PC_NAME = socket.gethostname()
if 'Win' == PC:
    IP = socket.gethostbyname(PC_NAME)
else:
    import requests
    IP = requests.get('http://globalip.me').text
    IP = IP[IP.find('curl globalip.me?ip'):]
    IP = IP[IP.find('<td'):]
    IP = IP[IP.find('>') + 1: IP.find('</td')].strip()

WEB_IP = '164.70.84.107'
DEV_IP = (IP if 'Win' == PC else '????')
MAC_IP = ('????' if IP in [DEV_IP, WEB_IP] else IP)

IPS = {DEV_IP: 'DEV', WEB_IP: 'Web', MAC_IP: 'Mac'}
IP_LIST = [DEV_IP, WEB_IP, MAC_IP]

CURRENT_PATH = {'Mac': '/Users/dsk_nagaoka/',
                'Win': 'C:/Users/dskna/'}
                # 'Win': 'C:/Users/Administrator/'}
# GDRIVE_PATH = {'Mac': CURRENT_PATH['Mac'] + 'Google ドライブ/',
GDRIVE_PATH = {'Mac': CURRENT_PATH['Mac'] + 'Library/CloudStorage/GoogleDrive-dsk.nagaoka.0226@gmail.com/マイドライブ/',
               'Win': 'G:/マイドライブ/'}
TEMP_PATH = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/',
             'Win': CURRENT_PATH['Win'] + 'Documents/MyToolTmp/'}
RUN_PATH = {'Mac': '/usr/local/bin/python3.13',
            'Win': CURRENT_PATH['Win'] + 'AppData/Local/Programs/Python/Python313/python.exe'}
            # 'Win': 'C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'}

# MT4のパス
MT4_PATH = CURRENT_PATH['Win'] + 'Documents/MT4/'
# 開発MT4のパス
MT4_DEV = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/',
           'Win': MT4_PATH + 'MT4_DEV/OANDA/'}
# パラメータ・集計データのCSV・HTML格納フォルダ
DATA_PATH = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/frame/',
             'Win': 'C:/inetpub/wwwroot/menu/frame/'}
# EAの単独テスト
TEST_UNIT = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/Test/',
             'Win': CURRENT_PATH['Win'] + 'Documents/Test/'}
# テスト集計データの出力先
TEST_OUT_PATH = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/out_test/',
                 'Win': 'C:/inetpub/wwwroot/test/'}
# テストリンク
TEST_LINK = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/Test/out_test/',
             'Win': 'http://' + DEV_IP + '/test/'}

# TickStoryのExeと作成先フォルダ
TICK_STORY = 'C:/Program Files (x86)/Tickstory/Tickstory.exe'
HST_PATH = {'Mac': GDRIVE_PATH['Mac'] + 'fx/history',
            'Win': GDRIVE_PATH['Win'] + 'fx/history'}

# アノマリー MT4パス
ANM_FOLD = '/anm/anomaly_'
ANM_PATH = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/test_root/ANM',
            'Win': CURRENT_PATH['Win'] + 'Documents/MT4/Web_MT4/MQL4/Files/ANM'}
# アノマリー MT4パス
ANM_OUT_PATH = {'Mac': CURRENT_PATH['Mac'] + 'MyToolTmp/test_root/MT4/anomaly',
                'Win': CURRENT_PATH['Win'] + 'Documents/apache-tomcat/webapps/ROOT/anomaly'}

# EAパラメータのファイルパス(Googleドライブ)
PRM_PATH = 'FX/Presets/'
# ReportManager
RM_PATH = CURRENT_PATH['Win'] + 'Documents/MT4/ReportManager/'
# テンプレートマッチングのパス
MATCH_PATH = 'item/match/'

# メニュー系CSV
MENU_CSV = {'Web': None, 'Fold': None, 'PwBank': None, 'PwWeb': None, 'Sql': None}

# アイコン
ICON_FILE = '/item/img/logo.ico'

