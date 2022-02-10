#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst
from common import times

import logging
import datetime


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
        format='%(asctime)s %(levelname)s[' + times.get_method() + '] %(message)s', level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(
            cst.TEMP_PATH[cst.PC] + 'Log/' +
            datetime.datetime.now().strftime('%Y-%m-%d').replace('-', '').split(' ')[0] + '.log')])
    return logger
