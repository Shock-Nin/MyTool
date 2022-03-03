#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import subprocess


class EaMergeTest:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        com.log(__name__)
        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        process = subprocess.Popen(cst.RM_PATH + '/reportmanager.exe')



        com.sleep(10)



        process.kill()

        com.close(self.myjob)
        return
