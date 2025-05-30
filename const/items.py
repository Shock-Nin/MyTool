#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 英単語再生、監視待機回数(3秒単位)
ENG1MIN_MONITOR = 20

# MT4立ち上げ待機時間
MT4_WAIT = [3, 15]

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
    'Logics選択': 'logics_select.png',
    'Risk選択': 'risk_select.png',
    '読み込み': 'read.png',
}
# ReportManagerマッチング
MATCH_IMG_RM = {'マージ': 'merge.png', '保存': 'save.png', 'ファイル': 'file.png', 'データ': 'data.png'}

# EA並び順
EA_PATHS = {'ShockninHimahima': ['Other'], 'ShockninIreguie': ['Main', 'Unit-']}
CURRENCIES_EA = [['EUR', 'GBP', 'AUD', 'JPY', 'GOLD'],
                 ['25', '25', '25', '25', '70']]
CURRENCIES_365 = ['JPY', 'EUR', 'GBP', 'AUD', 'CHF', 'CAD', 'NZD',
                  'ZAR', 'TRY', 'NOK', 'HKD', 'SEK', 'MXN', 'PLN']
EA_DATA_NAMES = ['EA個別成績', 'EA統合成績', 'EA統合年率']
EA_START_YM = '2007.01'
# EA_START_YM = '2005.01'

# くりっく365 CSV取引データ
RATE_CSV = 'https://www.tfx.co.jp/kawase/document/PRT-010-CSV-003-'
# くりっく365 リアルデータ
RATE_REAL = 'https://www.click365.jp/market.html'

# ブログ
BLOG_URL = 'https://shock-nin.info/'
# メール
BLOG_MAIL = 'shocknin7@gmail.com'
BLOG_MAIL_PW = 'Shock19800226'
ERROR_MAIL = 'shocknin7@gmail.com'
ERROR_MAIL_PW = 'kejm gyuz yczk dfcx'

# アノマリー Twitter
TWITTER_ID = '@ShockNin7'
TWITTER_PW = 'Shock19800226'
TWITTER_TAG = '#アノマリー #統計 #確率 #為替 #AI #学習'
TWEET_TIME = [20, 8]
# アノマリー 期間
ANM_SPAN = ['8-11', '12-15', '16-19', '20-23', '0-3', '4-7']
ANM_RANGE = ['15', '15']
ANM_AFTER = '12'
ANM_OPEN = 7
ANM_RATE = [4, 4, 6, 1]
ANM_HOUR_UD = 0.2
# アノマリー 確率差(0.1 = 55 %:45 %)
ANM_DIFF = 0.1
ANM_JUDGE = 0.5
# アノマリー レポート合格
ANM_BEST = 5
ANM_REPORT_UD = 0.2
DAY_WEEK = ['月', '火', '水', '木', '金']

# 英単語辞書URL(%s)
ENGLISH_USE_URL = 'https://free-liberty.com:1980/login'
ENGLISH_MASTER_URL = 'http://web.archive.org/web/20081219085629/http://www.alc.co.jp/goi/svl_l%s_list.htm'
ENGLISH_IMAGES_URL = 'https://www.google.com/search?q=%s+イメージ'
ENGLISH_MASTER_LEVEL = 12
ENGLISH_NOUNS = {'doushi': '動詞', 'meishi': '名詞', 'keiyoshi': '形容詞', 'fukushi': '副詞', 'zenchishi': '前置詞'}
# ENGLISH_IMAGES_URL = 'https://www.google.com/search?q=consequence+%E3%82%A4%E3%83%A1%E3%83%BC%E3%82%B8'

ENGLISH_DICT_URL = {
    'Google': ['https://translate.google.co.jp/?hl=ja&sl=en&tl=ja&text=%s&op=translate', '%s'],
    'Weblio': ['https://ejje.weblio.jp/content/%s', 'https://weblio.hs.llnwd.net/e8/audio/%s.mp3'],
    '英ナビ': ['https://www.ei-navi.jp/dictionary/content/%s', '%s'],
    '英辞郎': ['https://eow.alc.co.jp/search?q=%s', '%s'],
    'LONGMAN': ['https://www.ldoceonline.com/jp/dictionary/english-japanese/%s', 'https://www.ldoceonline.com/media/english/ameProns/%s.mp3'],
    '音読': ['', 'https://ondoku3.com/en/']
}

EINAVI_PARTSPEECH = {
    '動': '動詞', '助': '助動詞', '名': '名詞', '代': '代名詞', '疑': '疑問詞',
    '形': '形容詞', '副': '副詞', '前': '前置詞', '接': '接続詞', '限': '限定詞', '特': '限定詞'
}