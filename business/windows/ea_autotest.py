#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst


class EaAutotest:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        com.log(__name__)
        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        is_end = []
        if 0 < len(is_end):
            return com.close(is_end)

        return com.close(self.myjob)
