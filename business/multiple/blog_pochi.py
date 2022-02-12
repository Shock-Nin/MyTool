#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst


class BlogPochi:

    def __init__(self, job):
        self.myjob = job
        self.wd = com.driver()

    def do(self):
        com.log(__name__)
        self.wd.get(cst.BLOG_URL)

        is_end = []
        if 0 < len(is_end):
            return com.close(is_end)

        return com.close(self.myjob)
