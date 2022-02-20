#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst


class Batch:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        com.log(__name__)

        is_end = ()
        if 0 != is_end:
            return

        com.close(self.myjob)
