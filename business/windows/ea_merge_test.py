#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from common import com
from const import cst

import cv2
import subprocess
import pyautogui as pgui
import PySimpleGUI as sg
from PIL import ImageGrab

from business. windows import ea_edits as inheritance

IN_PATH = cst.TEST_OUT_PATH[cst.PC] + 'Merge/'
NAME_FILE = cst.DATA_PATH[cst.PC] + 'Unit.html'


class EaMergeTest:

    def __init__(self, job):
        self.myjob = job
        self.pos_xy = ['report.png', 'save.png']

    def do(self):

        tests = {}
        series = []
        paths = os.listdir(cst.TEST_OUT_PATH[cst.PC])

        name_list = inheritance.name_list(NAME_FILE)
        if name_list is None:
            return ['以下のファイルでエラーが発生しました。\n　' + NAME_FILE, '読み込みエラー', 'E']

        # テストデータの、フォルダとファイル名を取得
        for ea in cst.EA_PATHS:
            ea_fold = cst.EA_PATHS[ea][-1]

            for cur in cst.CURRNCYS_EA[0]:

                for path in paths:

                    if not os.path.isdir(cst.TEST_OUT_PATH[cst.PC] + path) \
                            or path.find(ea_fold) < 0 and path.find(cur) < 0:
                        continue

                    test_files = []
                    files = os.listdir(cst.TEST_OUT_PATH[cst.PC] + path)
                    for file in files:

                        if 0 <= file.find('htm'):
                            test_files.append(file)

                    test_files.sort()
                    tests[path] = test_files

        # 結合単位に、対象ファイルをまとめる
        targets = []
        for name in name_list:

            html = []
            for key in tests:
                files = tests[key]

                for file in files:
                    if name.lower() not in file:
                        continue

                    html.append(file)
            targets.append(html)

        alls = []
        for target in targets:
            for file in target:
                if 2 == len(file.split('_')[0]):
                    alls.append(file)

        targets.append(alls)
        name_list.append('All')
        targets.append(alls)
        name_list.append('Complete')
        print(targets)
        if com.question('開始しますか？\n\n　' + "\n　".join([name for name in name_list]), '開始確認') <= 0:
            return None

        # 進捗と中断の監視
        is_interrupt = False
        try:
            if 'Win' == cst.PC:
                process = subprocess.Popen(cst.RM_PATH + '/reportmanager.exe')
                com.sleep(2)
                process.kill()
                com.sleep(2)
                process = subprocess.Popen(cst.RM_PATH + '/reportmanager.exe')
                com.sleep(5)

            window = com.progress(self.myjob, ['', len(targets)], interrupt=True)

            while True:
                event, values = window.read(timeout=0)
                window[''].update()

                break

            # 中断イベント
            if _is_interrupt(window, event):
                is_interrupt = True
                return


        finally:
            try: process.kill()
            except: pass
            try: window.close()
            except: pass

        com.log(self.myjob + ': ' + ('全終了' if is_interrupt else '中断') + '(' + com.conv_time_str(total_time) + ')')
        com.dialog(('完了' if is_interrupt else '中断') + 'しました。(' + com.conv_time_str(total_time) + ')', self.myjob)
        return

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
