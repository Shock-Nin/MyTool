#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import subprocess

from business. windows import ea_edits as inheritance

EA_EXE = cst.MT4_DEV[cst.PC] + '/terminal.exe /portable'


class EaAutoTest:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        prm_lists = inheritance.prm_list()
        print(prm_lists)

        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        process = subprocess.Popen(EA_EXE)

        # while True:
        #     try:
        #         process.universal_newlines
        #         break
        #     except: pass

        print(str(process.universal_newlines))


        com.sleep(10)

        print(str(process.universal_newlines))


        process.kill()

        com.close(self.myjob)
        return
