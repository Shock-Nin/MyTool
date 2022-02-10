#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst


class BlogPochi:

    def __init__(self):
        self.wd = com.driver()

    def do(self):
        com.log(__name__)
        self.wd.get('https://shock-nin.info/')
        com.sleep(5)
        return []
