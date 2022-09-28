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

INFO_TOPIC = '食人のアノマリ〜つまみ食い！<br><br>'
ANM_URL = cst.BLOG_URL
# ANM_URL = ('http://localhost:8080/' if 'Mac' == cst.PC else cst.BLOG_URL)
ANM_URL += 'anomaly'
ANM_OUT_PATH = cst.ANM_OUT_PATH[cst.PC]
# ANM_OUT_PATH += 'test'
IS_TWEET = True
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
        self.now_day_str = ''
        self.my_span_str = ''

        self.anm_path = cst.ANM_PATH[cst.PC]

    def tweet(self):

        self._get_now_span()
        self._get_week_count()

        com.log('アノマリーTweet開始: ' +
            str(self.trade_y) + '-' + str(self.trade_m) + '-' + str(self.trade_d) + '(' +
            str(cst.DAY_WEEK[self.trade_w]) + str(self.trade_w) + ') ' + str(self.week_count) + 'w [' +
            str(self.trade_h) + 'h-' + str(self.now_span) + ', ' + str(cst.ANM_SPAN[self.now_span]) + ']')

        topic_texts = self._edit_topic_texts()
        if 0 == len(topic_texts):
            return ''

        try:
            msg = ''
            err_msg = ''

            for topic in topic_texts:
                topic = topic.replace('<br>', '\n')
                while 0 <= topic.find('<'):
                    topic = topic.replace(topic[topic.find('<'): topic.find('>') + 1], '')

                msg += topic.replace('&nbsp;', '')

            msg += '\n詳細・その他通貨、続きは ' + cst.BLOG_URL + '\n' + cst.TWITTER_TAG
            act = '1'

            # ウェブ操作スタート
            wd = web_driver.driver(headless=self.is_batch)
            if wd is None:
                com.log('WebDriverエラー', 'E')
                return None

            wd.get('https://twitter.com/intent/tweet?=' + cst.BLOG_URL +
                   '&text=' + urllib.parse.quote(msg, 'utf8'))
            com.sleep(5)
            act = '2, ' + wd.title

            web_driver.find_element(wd, 'session[username_or_email]').send_keys(cst.TWITTER_ID)
            web_driver.find_element(wd, 'session[password]').send_keys(cst.TWITTER_PW)
            act = '3, ' + wd.title

            web_driver.find_element(wd, '/html/body/div/div/div/div[1]/div[3]/div/div/div/div/div/div[2]/div[2]/div/div[2]/div[2]/div/span/span/span').click()
            com.sleep(5)
            act = '4, ' + wd.title

            if IS_TWEET:
                web_driver.find_element(wd, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div[3]/div/div[1]/div/div/div/div/div[2]/div[3]/div/div/div[2]/div[4]/div/span/span').click()
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
            if wd is None:
                com.log('WebDriverエラー', 'E')
                return None

            wd.get(ANM_URL)
            com.sleep(1)
            wd.get(ANM_URL)
            com.sleep(1)

            top_str = wd.page_source[wd.page_source.find('anomalyTitle'):]
            top_str = top_str[top_str.find('>') + 1: top_str.find('...')]

            guid_str = wd.page_source[wd.page_source.find('topicTop'):]
            guid_str = guid_str[guid_str.find('>') + 1: guid_str.find('</table>')]

            topic_texts.append(top_str + '、')
            topic_texts.append(guid_str)

            with open(ANM_OUT_PATH + '/topic.txt', 'w', encoding='utf8') as out:
                topic = "".join([txt for txt in topic_texts])
                out.write('食人のアノマリ〜つまみ食い！<br><br>' + topic[: topic.find('</td>')])

        except Exception as e:
            com.log('Topic取得エラー: ' + str(e), 'E')
            topic_texts = []
        finally:
            try: wd.quit()
            except: pass

        return topic_texts
