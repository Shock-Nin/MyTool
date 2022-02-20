#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import subprocess
from subprocess import PIPE

class EaAutotest:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        subprocess.run(os.getcwd() + '/venv/bin python' + '.py', shell=True, stdout=PIPE, stderr=PIPE, text=True)

        is_end = []
        if 0 < len(is_end):
            return com.close(is_end)

        return com.close(self.myjob)
