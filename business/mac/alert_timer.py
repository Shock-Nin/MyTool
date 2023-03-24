#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import os
import datetime
import PySimpleGUI as sg
from playsound import playsound

LIMIT_MIN = 60

class AlertTimer:

    def __init__(self, job):
        self.myjob = job
        com.log(self.myjob + ': 開始')

    def do(self):

        time_start = datetime.datetime.now()
        limit_min = LIMIT_MIN
        end_time = time_start + datetime.timedelta(minutes=limit_min)
        msg = str(com.str_time()) + ' - ' + str(end_time)[:-7]

        is_event = False
        window = self._window(msg, limit_min)

        try:
            # イベントループ
            while True:
                while datetime.datetime.now() < end_time:
                    com.sleep(1)

                    event, values = window.read(timeout=0)
                    window[str(limit_min) + '_'].update(
                        int(str(datetime.datetime.now() - time_start).split(':')[0]) * 60 +
                        int(str(datetime.datetime.now() - time_start).split(':')[1]))

                    # 画面のイベント監視
                    is_event = self._is_event(event)
                    if is_event is None:
                        return
                break
        finally:
            window.close()
            if is_event is None:
                com.log(self.myjob + ': 中断(' + str(int(str(end_time - datetime.datetime.now()).split(':')[0]) * 60 +
                        int(str(end_time - datetime.datetime.now()).split(':')[1])) + ')')
            else:
                com.log(self.myjob + ': 終了')
                window = self._comp(msg + '\n' + str(limit_min) + '分、終了しました。')

                # イベントループ
                while True:
                    event, values = window.read(timeout=0)
                    playsound(cst.CURRENT_PATH['Mac'] + 'MyTool/item/alert.mp3')

                    # 画面のイベント監視
                    is_event = self._is_event(event)
                    if is_event is None:
                        return

    def _window(self, text, limit_min):
        return sg.Window(self.myjob, keep_on_top=True, modal=True, background_color='#AAFFFF',
                         element_justification='c', margins=(5, 5), icon=(os.getcwd() + cst.ICON_FILE), layout=
                         [[sg.Text(text + '(' + str(limit_min) + ')', text_color='#000000',
                                   font=('', 12), background_color='#AAFFFF')],
                          [sg.ProgressBar(key=str(limit_min) + '_', max_value=limit_min, bar_color='#008000', size=(30, 20),
                                          pad=((15, 15), (5, 5)))]])

    def _comp(self, text):
        btn = [sg.Button('OK', key='OK', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#777777')]
        return sg.Window(self.myjob + ': 終了', keep_on_top=True, modal=True, background_color='#AAFFFF',
                         icon=(os.getcwd() + cst.ICON_FILE), return_keyboard_events=True, element_justification='c',
                         layout=[[sg.Text(text, background_color='#AAFFFF', text_color='#000000',
                                          font=('', 16), pad=((20, 20), (20, 10)))], btn])

    # イベントのアクション
    def _is_event(self, event):
        if event in ['OK', '\r', 'Return:603979789', sg.WIN_CLOSED]:
            return None
        return True
