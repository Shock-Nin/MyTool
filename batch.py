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
import datetime

from common import com
from const import cst

from business.multiple.blog_pochi import BlogPochi


class Batch:

    def __init__(self, job):
        self.myjob = job

    def do(self):
        now = datetime.datetime.now()
        jobs = []

        # 30分未満の場合にのみ実行
        if now.hour < 30:
            pass

        # 30分以上の場合にのみ実行
        else:

            # 毎朝3時にブログポチ
            if 3 == now.hour:
                if 0 == len(jobs):
                    com.log('Batch: 開始')
                BlogPochi(self.myjob).do()
                jobs.append('ブログポチ')

        return ", ".join([job for job in jobs])



