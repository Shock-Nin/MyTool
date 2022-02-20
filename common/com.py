#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst

import os
import logging
import inspect
import datetime

# スリープ直接呼び出し
from time import sleep

# display
from common import display
dialog = display.dialog
question = display.question
dialog_cols = display.dialog_cols
progress = display.progress
close = display.close

# matching
from common import matching
move_pos = matching.move_pos
click_pos = matching.click_pos
match = matching.match


# 日時を文字型で取得
def str_time(ymd=True):
    return datetime.datetime.now().strftime(('%Y-%m-%d ' if ymd else '') + '%H:%M:%S')


# 実行メソッドの取得
def get_method(before=0):
    stack = inspect.stack()[before + 2]
    file = stack.filename.replace(os.getcwd(), '')
    return file[1: file.rfind('.')] + '/' + stack.function


# ログをレベルに応じて出力
def log(msg, lv=''):
    logger = _format()
    msg = ' ' + get_method() + ' | ' + msg
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
        format='%(asctime)s [%(levelname)s]%(message)s', level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(
            cst.TEMP_PATH[cst.PC] + 'Log/' +
            datetime.datetime.now().strftime('%Y-%m-%d').replace('-', '').split(' ')[0] + '.log')])
    return logger


# ログフォルダの作成
if not os.path.exists(cst.TEMP_PATH[cst.PC]):
    os.mkdir(cst.TEMP_PATH[cst.PC])
