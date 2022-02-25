#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import cv2
import numpy as np
import pyautogui as pgui


# マウスを移動
def move_pos(x=None, y=None):
    pos_x, pos_y = pgui.position()
    try:
        if x is not None:
            pgui.moveTo(x, y)
        else:
            pgui.moveTo(pos_x, pos_y)
    except: pass


# クリックしてマウスを元位置に戻す
def click_pos(x=None, y=None):
    pos_x, pos_y = pgui.position()
    try:
        if x is not None:
            pgui.click(x, y, clicks=1, interval=0, button='left')
        pgui.moveTo(pos_x, pos_y)
    except: pass


# テンプレートマッチング
def match(shot, gray, tmp_path, color):

    tmp = cv2.imread(tmp_path, 0)
    res = cv2.matchTemplate(gray, tmp, cv2.TM_CCOEFF_NORMED)

    threshold = 0.99
    loc = np.where(threshold <= res)
    h, w = tmp.shape

    if 0 == len(loc[0]):
        print(com.str_time() + ' ' + tmp_path.replace(cst.TEMP_PATH[cst.PC], '') + ' : Nothing')
        return None, None

    # 出力ファイルに、マッチング場所をマーキング
    x = str(loc[1]).split(' ')[0].replace('[', '').replace(']', '')
    y = str(loc[0]).split(' ')[0].replace('[', '').replace(']', '')
    print(com.str_time() + ' ' + tmp_path.replace(cst.TEMP_PATH[cst.PC], '') + ' : ' + x + ' , ' + y)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(shot, pt, (pt[0] + w, pt[1] + h), color, 5)

    return int(x), int(y)
