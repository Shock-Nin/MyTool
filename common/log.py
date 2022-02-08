#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import os
import inspect
import logging
import datetime


def log(msg, lv=''):
    logger = _format()
    if 'E' == lv:
        logger.error(msg)
    elif 'W' == lv:
        logger.warning(msg)
    else:
        logger.info(msg)


# 実行メソッドの取得
def get_method(before=0):
    stack = inspect.stack()[before + 3]
    file = stack.filename.replace(os.getcwd(), '')
    return file[1: file.rfind('.')] + '/' + stack.function


def _format():
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format='%(asctime)s %(levelname)s[' + get_method() + '] %(message)s', level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(
            cst.TEMP_PATH[cst.PC] + 'Log/' +
            datetime.datetime.now().strftime('%Y-%m-%d').replace('-', '').split(' ')[0] + '.log')])
    return logger
