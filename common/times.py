#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime


def str_time(ymd=True):
    return datetime.datetime.now().strftime(('%Y-%m-%d ' if ymd else '') + '%H:%M:%S')
