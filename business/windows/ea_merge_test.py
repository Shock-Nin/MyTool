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

TEST_PATH = cst.TEST_OUT_PATH[cst.PC]
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

        # All(数字ロジックの個別の全結合)を追加
        alls = []
        for target in targets:
            for file in target:
                if 2 == len(file.split('_')[0]):
                    alls.append(file)

        targets.append(alls)
        name_list.append('All')

        if com.question('開始しますか？\n\n　' + "\n　".join([name for name in name_list]), '開始確認') <= 0:
            return None

        # 進捗と中断の監視
        is_interrupt = False
        total_time = 0
        try:
            start_time = com.time_start()

            if 'Win' == cst.PC:
                process = subprocess.Popen(cst.RM_PATH + '/reportmanager.exe')
                com.sleep(2)
                process.kill()
                com.sleep(2)
                process = subprocess.Popen(cst.RM_PATH + '/reportmanager.exe')
                com.sleep(5)

            while True:
                count = 0

                for key in cst.EA_PATHS:
                    ea_fold = cst.EA_PATHS[key][-1]

                    for i in range(count, len(targets)):
                        bar2 = targets[0][0].split('_')[0]
                        window = com.progress(self.myjob, ['ea', len(cst.EA_PATHS)], [bar2, len(targets[i])],
                                              interrupt=True)
                        event, values = window.read(timeout=0)

                        window['ea'].update(key)
                        window['ea_'].update(count)
                        window[bar2].update(targets[i][0].split('_')[0])
                        window[bar2 + '_'].update(i)

                        target_ea = targets[count][0].split('_')[0]

                        # 中断イベント
                        if _is_interrupt(window, event):
                            is_interrupt = True
                            return

                        if key.lower() == target_ea \
                                or (key.lower() != target_ea and i == len(targets) - 1):

                            self._call_report(ea_fold, targets[i], key.lower() == target_ea, True)
                            if key.lower() == target_ea:
                                break
                        else:
                            self._call_report(ea_fold, targets[i], ea_fold.find('-') < 0, False)

                    # 中断送り
                    if is_interrupt:
                        break
                    count += 1

                run_time = com.time_end(start_time)
                total_time += run_time

                break

        finally:
            try: process.kill()
            except: pass
            try: window.close()
            except: pass

        com.log(self.myjob + ': ' + ('全終了' if is_interrupt else '中断') + '(' + com.conv_time_str(total_time) + ')')
        com.dialog(('完了' if is_interrupt else '中断') + 'しました。(' + com.conv_time_str(total_time) + ')', self.myjob)
        return

    def _call_report(self, ea_fold, target, is_other, is_all):

        if is_all:
            if is_other:
                print(TEST_PATH + ea_fold + ' ' + str(target))
            else:
                for cur in cst.CURRNCYS_EA[0]:
                    print(TEST_PATH + ea_fold + cur + '/' + cur + ' ALL')
        else:
            if is_other:
                return

            for cur in cst.CURRNCYS_EA[0]:
                print(TEST_PATH + ea_fold + cur + '/' + "".join([file for file in target if 0 <= file.find(cur.lower())]))

        print(TEST_PATH + 'merge/' + ('all' if is_all and not is_other else target[0].split('_')[0]) + '.htm')

        print('-------------------')


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
