#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windowsタスクスケジューラ
　プログラム
　　C:/Users/Administrator/Documents/MyTool/venv/Scripts/python.exe
　　C:/Users/Administrator/Documents/MyTool/mytool.exe
　引数
　　mytool.py -f Batch
　　-f Batch
　開始
　　C:/Users/Administrator/Documents/MyTool
"""
from common import com
from const import cst

import datetime
import requests

from business.multiple.blog_pochi import BlogPochi


class Batch:

    def __init__(self, job):
        self.myjob = job
        self.now = datetime.datetime.now()
        self.my_ip = requests.get('https://ifconfig.me').text

    def do(self):

        jobs = []

        if 'Win' == cst.PC:
            job = self._windows()
            if 0 < len(job):
                jobs.append(job)

            # Web端末(5・35分)
            if cst.WEB_IP == self.my_ip:
                job = self._windows_web()
                if 0 < len(job):
                    jobs.append(job)

            # My端末(15・45分)
            if cst.MY_IP == self.my_ip:
                job = self._windows_my()
                if 0 < len(job):
                    jobs.append(job)

            # DEV端末(20・50分)
            if cst.DEV_IP == self.my_ip:
                job = self._windows_dev()
                if 0 < len(job):
                    jobs.append(job)

        return ", ".join([job for job in jobs])

    # WindpwsServer 共通バッチ
    def _windows(self):
        jobs = []

        # 30分未満の場合にのみ実行
        if self.now.minute < 30:
            pass

        # 30分以上の場合にのみ実行
        else:

            # 毎朝3時にブログポチ
            if 3 == self.now.hour:
                if 0 == len(jobs):
                    com.log('Batch開始: ' + self.my_ip)
                BlogPochi(self.myjob).do()
                jobs.append('ブログポチ')

        return ", ".join([job for job in jobs])

    # WindpwsServer Webバッチ(5・35分)
    def _windows_web(self):
        jobs = []

        # 土曜日12時～月曜4字まで休止
        if ((5 == self.now.weekday and 12 < self.now.hour)
                or 6 == self.now.weekday
                or (5 == self.now.weekday and self.now.hour < 4)):
            return jobs

        # 30分未満の場合にのみ実行
        if self.now.minute < 30:
            pass

        # 30分以上の場合にのみ実行
        else:
            pass

        return ", ".join([job for job in jobs])

    # WindpwsServer Myバッチ(15・45分)
    def _windows_my(self):
        jobs = []

        # 30分未満の場合にのみ実行
        if self.now.minute < 30:
            pass

        # 30分以上の場合にのみ実行
        else:
            pass

        return ", ".join([job for job in jobs])

    # WindpwsServer DEVバッチ(20・50分)
    def _windows_dev(self):
        jobs = []

        # 30分未満の場合にのみ実行
        if self.now.minute < 30:
            pass

        # 30分以上の場合にのみ実行
        else:
            pass

        return ", ".join([job for job in jobs])
