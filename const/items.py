#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 英単語再生、監視待機回数(3秒単位)
ENG1MIN_MONITOR = 20

# MT4立ち上げ待機時間
MT4_WAIT = [3, 10]

# MT4テンプレートマッチング
MATCH_IMG_MT4 = {
    '通貨': 'img_currency.png',
    '終了日': 'img_endday.png',
    '開始日': 'img_strday.png',
    '最適化ON': 'img_optchk.png',
    '最適化OFF': 'img_opt.png',
    'スプレッド': 'img_spread.png',
    'エキスパート': 'img_experts.png',
    'スタート': 'img_start.png',
    'ストップ': 'img_stop.png',
    'テスター': 'img_tester.png',
    'パラメータ': 'img_prm.png',
    '値': 'img_value.png',
    'Logics': 'img_logics.png',
    'Risk': 'img_risk.png',
    '読み込み': 'img_read.png',
}

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
