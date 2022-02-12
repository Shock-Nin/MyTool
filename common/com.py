#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst

import os
import logging
import inspect
import datetime
from time import sleep

# display
from common import display
dialog = display.dialog
question = display.question
progress = display.progress
close = display.close

# matching
from common import matching
move_pos = matching.move_pos
click_pos = matching.click_pos
match = matching.match

# web
from common import web
driver = web.driver
get_tag = web.get_tag
get_text = web.get_text


# 日時を文字型で取得
def str_time(ymd=True):
    return datetime.datetime.now().strftime(('%Y-%m-%d ' if ymd else '') + '%H:%M:%S')


# 実行メソッドの取得
def get_method(before=0):
    stack = inspect.stack()[before + 3]
    file = stack.filename.replace(os.getcwd(), '')
    return file[1: file.rfind('.')] + '/' + stack.function


# ログをレベルに応じて出力
def log(msg, lv=''):
    logger = _format()
    if 'E' == lv:
        logger.error(msg)
    elif 'W' == lv:
        logger.warning(msg)
    else:
        logger.info(msg)


# ログフォーマット
def _format():
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format='%(asctime)s %(levelname)s[' + get_method() + '] %(message)s', level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(
            cst.TEMP_PATH[cst.PC] + 'Log/' +
            datetime.datetime.now().strftime('%Y-%m-%d').replace('-', '').split(' ')[0] + '.log')])
    return logger
