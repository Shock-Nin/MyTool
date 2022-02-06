#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import cv2
import PySimpleGUI as sg
import pyautogui as pgui
import numpy as np

from time import sleep
from PIL import ImageGrab

TITLE = '英単語再生ループ'
FILE_PATH = '/Users/dsk_nagaoka/Public/'
WIN_X_MINUS = 350
WIN_Y_MINUS = 20


class Eng1Min:

    def __init__(self):
        self.win_x, self.win_y = pgui.size()
        self.turn = 0
        _write_log(TITLE + '　開始')
        sleep(2)

    def do_loop(self):

        window = self._window('　| |　')

        # イベントループ
        is_stop = False
        while True:

            event, values = window.read(timeout=0)

            if event == sg.WIN_CLOSED or 'end' == event:
                window.close()
                print(_get_time() + ' 終了')
                _write_log(TITLE + '　終了')
                return

            elif 'replay' == event:
                if '　| |　' == window['replay'].get_text():
                    is_stop = True
                    window.close()
                    print(_get_time() + ' 一時停止')
                    window = self._window('　▶︎　')
                    continue

                elif '　▶︎　' == window['replay'].get_text():
                    is_stop = False
                    window.close()
                    print(_get_time() + ' 再開')
                    window = self._window('　| |　')
                    continue

            if is_stop:
                sleep(5)
                continue

            ImageGrab.grab().save(FILE_PATH + 'shot.png')
            shot = cv2.imread(FILE_PATH + 'shot.png')
            gray = cv2.imread(FILE_PATH + 'shot.png', 0)
            is_end = False

            x, y = _do_match(shot, gray, FILE_PATH + 'replay.png', (255, 0, 255))
            if x is not None:
                is_end = True
                _move_pos(x / 2 + 20, y / 2 + 20)

            x, y = _do_match(shot, gray, FILE_PATH + 'end.png', (255, 0, 0))
            if x is not None:
                is_end = True
                _move_pos(x / 2 - 50, y / 2 + 20)

                self.turn += 1
                _write_log(TITLE + '　繰り返し(' + str(self.turn) + ')')

            if not is_end:

                x, y = _do_match(shot, gray, FILE_PATH + 'back.png', (0, 255, 255))
                if x is None:
                    sleep(2)

                    x, y = _do_match(shot, gray, FILE_PATH + 'icon1min.png', (0, 0, 255))
                    if x is not None:
                        _move_pos(x / 2 + 5, y / 2 + 10)
                        sleep(3)
                else:
                    _move_pos()

            cv2.imwrite(FILE_PATH + 'out.png', shot)
            window['turn'].update(str(self.turn) + '-' + _get_time(False))
            sleep(5)

    def _window(self, stop_btn):
        return sg.Window(
            TITLE, keep_on_top=True, modal=True,
            location=(self.win_x - WIN_X_MINUS, self.win_y - WIN_Y_MINUS),
            layout=[[sg.Button(stop_btn, key='replay', font=('', 16)),
                     sg.Text(' ' + str(self.turn) + ' ', key='turn', font=('', 16)),
                     sg.Button('　■　', key='end', font=('', 16))]]
        )


def _move_pos(x=None, y=None):
    pos_x, pos_y = pgui.position()
    try:
        if x is not None:
            pgui.click(x, y, clicks=1, interval=0, button='left')
        pgui.moveTo(pos_x, pos_y)
    except:
        pass


def _do_match(shot, gray, tmp_path, color):

    tmp = cv2.imread(tmp_path, 0)
    res = cv2.matchTemplate(gray, tmp, cv2.TM_CCOEFF_NORMED)

    threshold = 0.99
    loc = np.where(threshold <= res)
    h, w = tmp.shape

    if 0 == len(loc[0]):
        print(_get_time() + ' ' + tmp_path.replace(FILE_PATH, '') + ' : Nothing')
        return None, None

    x = str(loc[1]).split(' ')[0].replace('[', '').replace(']', '')
    y = str(loc[0]).split(' ')[0].replace('[', '').replace(']', '')
    print(_get_time() + ' ' + tmp_path.replace(FILE_PATH, '') + ' : ' + x + ' , ' + y)
    for pt in zip(*loc[::-1]):
        cv2.rectangle(shot, pt, (pt[0] + w, pt[1] + h), color, 5)

    return int(x), int(y)


def _write_log(msg):
    log = open('/Users/Log/MyTools/' + _get_time().replace('-', '').split(' ')[0] + '.log', 'a', encoding='UTF-8')
    log.write(_get_time() + ' ' + msg + '\n')
    log.close()


def _get_time(ymd=True):
    return datetime.datetime.now().strftime(('%Y-%m-%d ' if ymd else '') + '%H:%M:%S')
