#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

from common import com
from const import cst

import os
import pyautogui as pgui
import TkEasyGUI as sg

from common import web_driver

WIN_X_MINUS = 50
BGCOLOR_ON = '#AAFFFF'
BGCOLOR_OFF = '#FF7777'


class KeepDisplay:

    def __init__(self, job):
        self.myjob = job
        self.bgcolor = BGCOLOR_ON
        self.turn = 0
        self.move = 0
        self.win_x, self.win_y = pgui.size()
        self.now_x, self.now_y = pgui.position()
        self.last_x, self.last_y = pgui.position()
        com.log(self.myjob + ': 開始')
        com.sleep(2)

    def do(self):

        window = self._window('　| |　')
        is_stop = False

        # イベントループ
        while True:

            event, values = window.read(timeout=0)
            is_normal, is_stop, window = self._is_event(window, event, is_stop)

            # 画面のイベント監視
            if is_normal is None:
                if window is None:
                    return
                else:
                    if is_stop is not None:
                        continue
            elif is_stop:
                com.sleep(3)
                continue

            com.click_pos()

    def _window(self, stop_btn):
        return sg.Window(self.myjob, keep_on_top=True, modal=True, background_color=self.bgcolor,
                         location=(self.win_x - 50, self.win_y), margins=(5, 5), icon=(os.getcwd() + cst.ICON_FILE), layout=
                         [[sg.Button(stop_btn, key='replay', font=('', 12), pad=((0, 0), (0, 0)))]])

    # イベントのアクション
    def _is_event(self, window, event, is_stop):

        if event == sg.WIN_CLOSED:
            window.close()
            com.log(self.myjob + ': 終了')
            return None, None, None

        elif 'replay' == event:
            if '　| |　' == window['replay'].get_text():
                com.log(self.myjob + ': 一時停止')
                self.bgcolor = BGCOLOR_OFF
                window.close()
                return None, True, self._window('　▶︎　')

            elif '　▶︎　' == window['replay'].get_text():
                com.log(self.myjob + ': 再開')
                self.bgcolor = BGCOLOR_ON
                window.close()
                return None, False, self._window('　| |　')

        return True, is_stop, window
