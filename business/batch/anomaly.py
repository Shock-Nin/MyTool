#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
バッチ
アノマリーのトピック作成(ブラウザ)取得、DB登録
"""
from common import com
from const import cst
from common import web_driver

import datetime
import urllib.parse

INFO_TOPIC = 'アノマリ〜食人の%sつまみ食い！<br>'
ANM_URL = cst.BLOG_URL + 'anomaly'
# ANM_URL = 'file:///Users/dsk_nagaoka/MyToolTmp/test_root/MT4/Trender/anomaly/index.html'

# 0デフォルト、1通常アノマリー、2ゴトー日、3社会のマド
TWEET_TEST_TYPE = 0
ANM_OUT_PATH = cst.ANM_OUT_PATH[cst.PC]
IS_TWEET = (0 == TWEET_TEST_TYPE)
# IS_TWEET = False


class Anomaly:

    def __init__(self, job):
        self.myjob = job
        self.is_batch = ('Batch' == job)

        self.trade_now = datetime.datetime.now()
        # self.trade_now = datetime.datetime.strptime(
        #     self.trade_now.strftime('%Y%m') + '06' + ' ' + '22' + self.trade_now.strftime('%M%S'), '%Y%m%d %H%M%S')
        self.trade_y = self.trade_now.year
        self.trade_m = self.trade_now.month
        self.trade_d = self.trade_now.day
        self.trade_w = self.trade_now.weekday()
        self.trade_h = self.trade_now.hour
        self.week_count = 0
        self.now_span = 0
        self.now_day_str = ''
        self.my_span_str = ''

        self.anm_path = cst.ANM_PATH[cst.PC]

    # トピック書き出し
    def write_topic(self):

        self.__get_now_span()
        self.__get_week_count()

        com.log('アノマリーTopic作成開始: ' +
            str(self.trade_y) + '-' + str(self.trade_m) + '-' + str(self.trade_d) + '(' +
            str(cst.DAY_WEEK[self.trade_w]) + str(self.trade_w) + ') ' + str(self.week_count) + 'w [' +
            str(self.trade_h) + 'h-' + str(self.now_span) + ', ' + str(cst.ANM_SPAN[self.now_span]) + ']')

        try:
            # ウェブ操作スタート
            wd = web_driver.driver(headless=self.is_batch)
            if wd is None:
                com.log('WebDriverエラー', 'E')
                return None

            wd.get(ANM_URL)
            com.sleep(1)
            wd.get(ANM_URL)
            com.sleep(1)

            topic_text = wd.page_source[wd.page_source.find('topicText'):]
            topic_text = topic_text[topic_text.find('>') + 1: topic_text.find('</p>')]
            topic_day = topic_text[: topic_text.find('の')]
            topic_text = topic_text[topic_text.find('、') + 1:]

            shakaymado_str = wd.page_source[wd.page_source.find('topicShakaymadoText'):]
            shakaymado_str = shakaymado_str[shakaymado_str.find('>') + 1: shakaymado_str.find('</p>')]
            shakaymado_str = ('' if len(shakaymado_str) < 10 else
                              shakaymado_str.replace('週目', '').replace('週', '').replace('スタートは', '月曜日、スタートで'))

            gotobe_str = wd.page_source[wd.page_source.find('topicGotobeText'):]
            gotobe_str = gotobe_str[gotobe_str.find('>') + 1: gotobe_str.find('</p>')]
            gotobe_str = ('' if len(gotobe_str) < 10 else '今回のゴト〜日は、' + gotobe_str)

            with open(ANM_OUT_PATH + '/topic.txt', 'w', encoding='utf8') as out:
                out.write((INFO_TOPIC % topic_day) + '<br>' + topic_text)
            with open(ANM_OUT_PATH + '/topic_special.txt', 'w', encoding='utf8') as out:
                out.write('<br><br>' + shakaymado_str + '<br><br>\n\n' + gotobe_str)

        except Exception as e:
            com.log('Topic取得エラー: ' + str(e), 'E')
        finally:
            try: wd.quit()
            except: pass

        return ''

    # ツイート
    def tweet(self):

        tweet_type = 0
        # 月曜〜金曜の0時と12時に、通常アノマリーツイート実行
        if self.trade_h in [0, 12]:
            tweet_type = 1

        # ゴトー日の2時に、ゴトー日アノマリー実行
        elif 2 == self.trade_h and self.trade_d in [0, 5, 10, 15, 20, 25, 29, 30, 31]:
            tweet_type = 2

        # 月曜の4時に、社会のマドアノマリー実行
        elif 4 == self.trade_h and 0 == self.trade_w:
            tweet_type = 3

        tweet_type = (tweet_type if 0 == TWEET_TEST_TYPE else TWEET_TEST_TYPE)
        if 0 < tweet_type:
            msg = ''
            err_msg = ''

            try:
                with open(ANM_OUT_PATH + '/topic' + ('' if 1 == tweet_type else '_special') +
                          '.txt', 'r', encoding='utf8') as read_file:
                    topics = read_file.read().split('\n')

                for i in range(0, len(topics)):
                    if 1 != tweet_type and i != (0 if 2 == tweet_type else 2):
                        continue

                    topic = topics[i].replace('<br>', '\n')

                    while 0 <= topic.find('<'):
                        topic = topic.replace(topic[topic.find('<'): topic.find('>') + 1], '')

                    if 1 < tweet_type:
                        while 0 <= topic.find('('):
                            topic = topic.replace(topic[topic.find('('): topic.find(')') + 1], '')

                    msg += topic.replace('&nbsp;', '')

                if 0 == len(msg):
                    return ''

                if 1 < tweet_type:
                    with open(ANM_OUT_PATH + '/topic.txt', 'r', encoding='utf8') as read_file:
                        topic = read_file.read().split('\n')[0].split('<br>')[0]

                        while 0 <= topic.find('<'):
                            topic = topic.replace(topic[topic.find('<'): topic.find('>') + 1], '')
                        msg = topic + '\n' + msg

                msg += '\n詳細・その他通貨、続きは ' + cst.BLOG_URL + '\n' + cst.TWITTER_TAG
                msg = msg.replace('\n\n', '\n').replace('\n\n', '\n')
                act = '1'

                if 0 < TWEET_TEST_TYPE:
                    print(msg)
                    return ''

                # ウェブ操作スタート
                wd = web_driver.driver(headless=self.is_batch)
                # wd = web_driver.driver()
                if wd is None:
                    com.log('WebDriverエラー', 'E')
                    return None

                # wd.get('https://x.com/intent/tweet?=https://shock-nin.info/&text=aaaaa')
                wd.get('https://x.com/intent/tweet?=' + cst.BLOG_URL +
                       '&text=' + urllib.parse.quote(msg, 'utf8'))
                com.sleep(5)
                act = '2, ' + wd.title

                web_driver.find_element(wd, '//*[@id="layers"]/div[3]/div/div/div/div/div/div[2]/div[2]/div/div[2]/button[2]/div/span/span/span').click()
                com.sleep(5)

                xpath = '//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/'
                web_driver.find_element(wd, xpath + 'div/div/div/div[4]/label/div/div[2]/div/input').send_keys(cst.TWITTER_ID)
                web_driver.find_element(wd, xpath + 'div/div/div/button[2]').click()
                com.sleep(3)
                act = '3, ' + wd.title
                web_driver.find_element(wd, xpath + 'div[1]/div/div/div[3]/div/label/div/div[2]/div[1]/input').send_keys(cst.TWITTER_PW)
                web_driver.find_element(wd, xpath + 'div[2]/div/div[1]/div/div/button').click()
                com.sleep(3)
                act = '4, ' + wd.title

                if IS_TWEET:
                    web_driver.find_element('/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[3]/div[2]/div[1]/div/div/div/div[2]/div[2]/div/div/div/button[2]').click()
                    com.sleep(3)
                    act = '5, ' + wd.title
                    com.log('アノマリーTweet(' + act + ')' + msg.replace('\n', '<br>'))

            except Exception as e:
                err_msg = ' エラー発生(' + act + ') ' + str(e)

            finally:
                try: wd.quit()
                except: pass

            com.log('アノマリーTweet [' + self.now_day_str + ' ' + self.my_span_str + 'h]' +
                    (' 完了' if 0 == len(err_msg) else err_msg), lv=('' if 0 == len(err_msg) else 'E'))

        return ''

    # 時間帯変換
    def __get_now_span(self):
        self.now_span = (4 if self.trade_h < 2 else 5 if self.trade_h < 6 else 0 if self.trade_h < 10 else
                         1 if self.trade_h < 14 else 2 if self.trade_h < 18 else 3 if self.trade_h < 22 else 4)

        self.trade_now -= (datetime.timedelta(days=(1 if self.trade_h < 6 else 0)))
        self.trade_w = self.trade_now.weekday()

        if 5 <= self.trade_now.weekday():
            self.now_span = 0

        while True:
            if self.trade_now.weekday() < 5:
                break
            self.trade_now = self.trade_now + datetime.timedelta(days=1)

        self.trade_y = self.trade_now.year
        self.trade_m = self.trade_now.month
        self.trade_d = self.trade_now.day
        self.trade_w = self.trade_now.weekday()

    # 月の週目算出
    def __get_week_count(self):

        self.week_count = 1
        w_date = self.trade_now.strftime('%Y%m')
        w_date = datetime.datetime.strptime(w_date + '01', '%Y%m%d')

        for i in range(1, self.trade_now.day):

            if w_date.weekday() == self.trade_now.weekday():
                self.week_count += 1
            w_date = w_date + datetime.timedelta(days=1)
