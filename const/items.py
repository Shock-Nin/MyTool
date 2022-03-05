#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 英単語再生、監視待機回数(3秒単位)
ENG1MIN_MONITOR = 20

# MT4立ち上げ待機時間
MT4_WAIT = [3, 10]

# MT4テンプレートマッチング
MATCH_IMG_MT4 = {
    '通貨': 'currency.png',
    '終了日': 'endday.png',
    '開始日': 'startday.png',
    '最適化ON': 'optchk.png',
    '最適化OFF': 'opt.png',
    'スプレッド': 'spread.png',
    'エキスパート': 'experts.png',
    'レポート': 'report.png',
    'スタート': 'start.png',
    'ストップ': 'stop.png',
    'パラメータ': 'prm.png',
    '値': 'value.png',
    'Logics': 'logics.png',
    'Risk': 'risk.png',
    '読み込み': 'read.png',
}
# ReportManagerマッチング
MATCH_IMG_RM = {'マージ': 'merge.png', '保存': 'save.png', 'ファイル': 'file.png', 'データ': 'data.png'}

# EA並び順
EA_PATHS = {'AnomalyGoToBe': ['Other'], 'AnomalyShocknin': ['Main', 'Unit-']}
CURRNCYS_EA = [['EUR', 'GBP', 'AUD', 'NZD', 'JPY', 'CHF', 'CAD', 'GOLD'],
               ['25', '25', '25', '25', '25', '25', '25', '70']]
CURRNCYS_365 = ['JPY', 'EUR', 'GBP', 'AUD', 'CHF', 'CAD', 'NZD',
                'ZAR', 'TRY', 'NOK', 'HKD', 'SEK', 'MXN', 'PLN']
EA_DATA_NAMES = ['EA個別成績', 'EA統合成績', 'EA統合年率']

# ブログ
BLOG_URL = 'https://shock-nin.info/'

# メール
BLOG_MAIL = 'shocknin7@gmail.com'
BLOG_MAIL_PW = 'Shock19800226'
ERROR_MAIL = 'error19800226@gmail.com'
ERROR_MAIL_PW = 'Error@1980'
