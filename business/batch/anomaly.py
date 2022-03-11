#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst
from common import web_driver

import datetime
import pyautogui as pgui
import urllib.parse

INFO_TOPIC = '食人のアノマリ〜つまみ食い！<br><br>'
ANM_URL = cst.BLOG_URL
# ANM_URL = ('http://localhost:8080/' if 'Mac' == cst.PC else cst.BLOG_URL)
ANM_URL += 'anomaly'
ANM_OUT_PATH = cst.ANM_OUT_PATH[cst.PC]
# ANM_OUT_PATH += 'test'
IS_TWEET = False
# IS_TWEET = True


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

        self.anm_path = cst.ANM_PATH[cst.PC]

    def create(self):

        com.log('Anomaly開始')
        self._get_now_span()
        self._get_week_count()

        com.log(
            str(self.trade_y) + '-' + str(self.trade_m) + '-' + str(self.trade_d) + '(' +
            str(cst.DAY_WEEK[self.trade_w]) + str(self.trade_w) + ') ' + str(self.week_count) + 'w [' +
            str(self.trade_h) + 'h-' + str(self.now_span) + ', ' + str(cst.ANM_SPAN[self.now_span]) + ']')

        # 日時条件設定
        now_day_str = str(self.trade_d) + '日'
        my_span_str = cst.ANM_SPAN[self.now_span]

        topic_texts = self._edit_topic_texts()

        self._output_topic(topic_texts)

        com.log(now_day_str + ' ' + str(self.trade_h) + 'h[' + my_span_str + ']完了しました。')

        return topic_texts

    # 時間帯変換
    def _get_now_span(self):
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
    def _get_week_count(self):

        self.week_count = 1
        w_date = self.trade_now.strftime('%Y%m')
        w_date = datetime.datetime.strptime(w_date + '01', '%Y%m%d')

        for i in range(1, self.trade_now.day):

            if w_date.weekday() == self.trade_now.weekday():
                self.week_count += 1
            w_date = w_date + datetime.timedelta(days=1)

    # アノマリー Topic
    def _edit_topic_texts(self):

        topic_texts = []
        try:
            # ウェブ操作スタート
            wd = web_driver.driver(headless=self.is_batch)
            # wd = web_driver.driver()
            if wd is None:
                com.log('WebDriverエラー', 'E')
                return

            wd.get(ANM_URL)
            com.sleep(1)
            wd.get(ANM_URL)
            com.sleep(1)

            top_str = wd.page_source[wd.page_source.find('anomalyData'):]
            guid_str = ''

            if 0 <= top_str.find('基本スタンス'):
                guid_str = top_str[top_str.find('基本スタンス') + 7:]
                guid_str = guid_str[:guid_str.find('<br>')]

            top_str = top_str[top_str.find('>') + 1: top_str.find('週は') - 10]
            top_str = top_str.replace('のアノマリ〜', '')

            topic_texts.append(top_str)
            topic_texts.append(guid_str)

        except Exception as e:
            com.log('Topic取得エラー: ' + str(e), 'E')
        finally:
            try: wd.quit()
            except: pass

        return topic_texts

    # アノマリー トップページ出力
    def _output_topic(self, topic_texts):

        try:
            out_txt = INFO_TOPIC
            out_txt += (topic_texts[0].replace('！', 'につき' + topic_texts[1])
                        if 0 <= topic_texts[0].find('！') else topic_texts[0])

            with open(ANM_OUT_PATH + '/topic.txt', 'w', encoding='UTF-8') as f:
                f.write(out_txt)

        except Exception as e:
            com.log('Topic出力エラー: ' + str(e), 'E')

    def tweet(self, topic_texts):

        msg = ''
        for topic in topic_texts:
            topic = topic.replace('<br>', '\n')
            while 0 <= topic.find('<'):
                topic = topic.replace(topic[topic.find('<'): topic.find('>') + 1], '')

            msg += topic + '\n'

        msg += '\n詳細・その他通貨、続きは ' + cst.BLOG_URL + '\n' + cst.TWITTER_TAG

        act = '1'
        try:
            # ウェブ操作スタート
            wd = web_driver.driver(headless=self.is_batch)
            # wd = web_driver.driver()
            if wd is None:
                com.log('WebDriverエラー', 'E')
                return

            wd.get('https://twitter.com/intent/tweet?=' + cst.BLOG_URL +
                   '&text=' + urllib.parse.quote(msg, 'UTF-8'))
            act = '2'
            com.sleep(10)

            com.clip_copy('')
            pgui.hotkey('ctrl' if 'Win' == cst.PC else 'command', 'a')
            pgui.write('')
            com.sleep(1)
            com.clip_copy(cst.TWITTER_ID)
            pgui.hotkey('tab')
            com.sleep(1)
            com.clip_copy(cst.TWITTER_PASS)
            act = '3'
            com.sleep(2)

            pgui.hotkey('tab')
            pgui.hotkey('tab')
            pgui.hotkey('tab')
            pgui.hotkey('enter')
            act = '4'
            com.sleep(15)

            if IS_TWEET:
                wd.find_element('//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[3]/div/div[1]/div/div/div/div/div[2]/div[3]/div/div/div[2]/div[4]/div/span/span').click()
                act = '5'
                com.sleep(2)

        except Exception as e:
            com.log('ツイート送信エラー発生(' + act + ') ' + str(e))
            return False

        finally:
            try: wd.quit()
            except: pass

        return True