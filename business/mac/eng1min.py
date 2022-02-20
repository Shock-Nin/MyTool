#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import os
import cv2
import pyautogui as pgui
import PySimpleGUI as sg

from time import sleep
from PIL import ImageGrab

IMG_PATH = 'item/match/eng1min/'
WIN_X_MINUS = 50
BGCOLOR_ON = '#AAFFFF'
BGCOLOR_OFF = '#FF7777'


class Eng1min:

    def __init__(self, job):
        self.myjob = job
        self.bgcolor = BGCOLOR_ON
        self.turn = 0
        self.move = 0
        self.win_x, self.win_y = pgui.size()
        self.now_x, self.now_y = pgui.position()
        self.last_x, self.last_y = pgui.position()
        com.log(self.myjob + ': 開始')
        sleep(2)

    def do(self):

        window = self._window('| |')
        is_stop = False

        # イベントループ
        while True:

            event, values = window.read(timeout=0)
            is_normal, is_stop, window = self._is_evwnt(window, event, is_stop)

            # 画面のイベント監視
            if is_normal is None:
                if window is None:
                    return
                else:
                    if is_stop is not None:
                        continue
            elif is_stop:
                sleep(3)
                continue

            # 不動時間のカウント
            self.now_x, self.now_y = pgui.position()
            if self.last_x == self.now_x and self.last_y == self.now_y:
                sleep(3)
                self.move += 1

                # 画面のイベント監視
                if is_normal is None:
                    if window is None:
                        return
                    else:
                        if is_stop is not None:
                            continue
                elif is_stop:
                    sleep(3)
                    continue
            else:
                self.move = 0
                self.last_x, self.last_y = pgui.position()
            window['turn'].update(' ' + str(self.turn) + '\n ' + str(int(self.move / 20)))

            # 監視待機回数未満なら動作なし
            if self.move < cst.ENG1MIN_MONITOR:
                if 0 == self.move % 5:
                    print('Move: ' + str(self.move))
                continue

            # 全体画面の撮影
            shot_path = cst.TEMP_PATH[cst.PC] + 'shot.png'
            ImageGrab.grab().save(shot_path)
            shot = cv2.imread(shot_path)
            gray = cv2.imread(shot_path, 0)
            is_end = False

            # もう一度再生とのマッチング
            x, y = com.match(shot, gray, IMG_PATH + 'replay.png', (255, 0, 255))
            if x is not None:
                is_end = True
                com.click_pos(x / 2 + 20, y / 2 + 20)

            # 終了画面とのマッチング
            x, y = com.match(shot, gray, IMG_PATH + 'end.png', (255, 0, 0))
            if x is not None:
                is_end = True
                com.click_pos(x / 2 - 50, y / 2 + 20)

                self.turn += 1
                window['turn'].update(self.turn)
                com.log(self.myjob + ': 繰り返し(' + str(self.turn) + ')')

            # 画面のイベント監視
            if is_normal is None:
                if window is None:
                    return
                else:
                    if is_stop is not None:
                        continue
            elif is_stop:
                sleep(3)
                continue

            # 終了系とのマッチングがなかった場合
            if not is_end:

                # アプリ全面表示用のマッチング
                x, y = com.match(shot, gray, IMG_PATH + 'back.png', (0, 255, 255))
                if x is None:
                    sleep(2)

                    # アプリアイコンのマッチング
                    x, y = com.match(shot, gray, IMG_PATH + 'icon1min.png', (0, 0, 255))
                    if x is not None:
                        com.click_pos(x / 2 + 5, y / 2 + 10)
                        sleep(3)
                else:
                    com.move_pos()

            # マッチングのマーキングimg出力
            cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)

            # 画面のイベント監視
            if is_normal is None:
                if window is None:
                    return
                else:
                    if is_stop is not None:
                        continue
            if not is_end:
                sleep(3)

    def _window(self, stop_btn):
        return sg.Window(self.myjob, keep_on_top=True, modal=True, background_color=self.bgcolor,
                         location=(self.win_x - 50, 0), margins=(5, 5), icon=(os.getcwd() + cst.ICON_FILE), layout=
                         [[sg.Button(stop_btn, key='replay', font=('', 12), pad=((0, 0), (0, 0))),
                          sg.Text(' ' + str(self.turn) + '\n ' + str(int(self.move / 20)), key='turn', size=(2, 0), pad=((0, 0), (0, 0)),
                          background_color=self.bgcolor, text_color='#000000')]])

    # イベントのアクション
    def _is_evwnt(self, window, event, is_stop):

        if event == sg.WIN_CLOSED:
            window.close()
            com.log(self.myjob + ': 終了')
            return None, None, None

        elif 'replay' == event:
            if '| |' == window['replay'].get_text():
                com.log(self.myjob + ': 一時停止')
                self.bgcolor = BGCOLOR_OFF
                window.close()
                return None, True, self._window('▶︎')

            elif '▶︎' == window['replay'].get_text():
                com.log(self.myjob + ': 再開')
                self.bgcolor = BGCOLOR_ON
                window.close()
                return None, False, self._window('| |')

        return True, is_stop, window
