#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windowsタスクスケジューラ
　プログラム
　　C:/Users/Administrator/Documents/MyTool/mytool.exe
　引数
　　-f Batch
　開始
　　C:/Users/Administrator/Documents/MyTool
　実行コマンド
　　cd C:/Users/Administrator/Documents/MyTool; python mytool.py -f Batch
　　cd dsk_nagaoka@MacBookAir202012 MyTool; python mytool.py -f Batch
"""
from common import com
from const import cst

from business.batch.anomaly import Anomaly
from business.batch.saya_daily import SayaDaily
from business.batch.saya_timely import SayaTimely

import datetime


class Batch:

    def __init__(self, job):
        self.myjob = job
        self.now = datetime.datetime.now()

    def do(self):
        jobs = []

        if 'Win' == cst.PC:
            job = self.__windows()
            if 0 < len(job):
                jobs.append(job)

            # Web端末(5・35分)
            if cst.WEB_IP == cst.IP:
                job = self.__windows_web()
                if 0 < len(job):
                    jobs.append(job)

            # My端末(15・45分)
            if cst.MY_IP == cst.IP:
                job = self.__windows_my()
                if 0 < len(job):
                    jobs.append(job)

            # DEV端末(20・50分)
            if cst.DEV_IP == cst.IP:
                job = self.__windows_dev()
                if 0 < len(job):
                    jobs.append(job)

        return ", ".join([job for job in jobs])

    # WindowsServer 共通バッチ
    def __windows(self):
        jobs = []

        # 30分未満の場合にのみ実行
        if self.now.minute < 30:
            pass

        # 30分以上の場合にのみ実行
        else:
            pass

        return ", ".join([job for job in jobs])

    # WindowsServer Webバッチ(5・35分)
    def __windows_web(self):
        jobs = []


        # 30分未満の場合に実行
        if self.now.minute < 30:

            # 9・11時に実行
            if self.now.hour in [9, 11]:

                if 0 == len(jobs):
                    com.log('Batch開始: ' + cst.IP)

                SayaDaily(self.myjob).get_csv()
                jobs.append('365日足更新')

            # 0時にトピック作成
            if 0 == self.now.hour:
                if 0 == len(jobs):
                    com.log('Batch開始: ' + cst.IP)

                Anomaly(self.myjob).write_topic()
                jobs.append('アノマリーTopic作成')

        # 30分以上の場合に実行
        else:
            # 元旦とクリスマス以外の平日に実行
            if self.now.weekday() < 5 \
                    and not (1 == self.now.month and 1 == self.now.day) \
                    and not (12 == self.now.month and 25 == self.now.day):

                # 月曜〜金曜の3・6時・12時に実行
                if self.now.hour in [0, 12, 3]:

                    if 0 == len(jobs):
                        com.log('Batch開始: ' + cst.IP)

                    Anomaly(self.myjob).tweet()
                    jobs.append('アノマリーTweet')

        # 30分間隔で実行
        if 0 == len(jobs):
            com.log('Batch開始: ' + cst.IP)

        SayaTimely(self.myjob).get_web()
        jobs.append('365リアル更新')

        return ", ".join([job for job in jobs])

    # WindowsServer Myバッチ(15・45分)
    def __windows_my(self):
        jobs = []

        return ", ".join([job for job in jobs])

    # WindowsServer DEVバッチ(20・50分)
    def __windows_dev(self):
        jobs = []

        # 30分未満の場合にのみ実行
        if self.now.minute < 30:
            pass

        # 30分以上の場合にのみ実行
        else:
            pass

        return ", ".join([job for job in jobs])
