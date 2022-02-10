#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import inspect
import datetime


# 日時を文字型で取得
def str_time(ymd=True):
    return datetime.datetime.now().strftime(('%Y-%m-%d ' if ymd else '') + '%H:%M:%S')


# 実行メソッドの取得
def get_method(before=0):
    stack = inspect.stack()[before + 3]
    file = stack.filename.replace(os.getcwd(), '')
    return file[1: file.rfind('.')] + '/' + stack.function
