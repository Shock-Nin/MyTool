#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from common import com
from const import cst

import cv2
import subprocess
import pyautogui as pgui
import PySimpleGUI as sg

from business. windows import ea_edits as inheritance

TEST_PATH = cst.TEST_OUT_PATH[cst.PC]
NAME_FILE = cst.DATA_PATH[cst.PC] + 'Unit.html'


class EaMergeTest:

    def __init__(self, job):
        self.myjob = job
        self.pos_xy = cst.MATCH_IMG_RM.copy()

    def do(self):

        tests = {}
        paths = os.listdir(cst.TEST_OUT_PATH[cst.PC])

        # EAの名前リストを取得
        name_list = inheritance.name_list(NAME_FILE)
        if name_list is None:
            com.dialog('以下のファイルでエラーが発生しました。\n　' + NAME_FILE, '読み込みエラー', 'E')
            return

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
            return

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

                # 全体画面の撮影
                shot, gray = com.shot_grab()
                if shot is None:
                    return

                # テンプレートマッチング
                for key in cst.MATCH_IMG_RM:
                    self.pos_xy[key] = com.match(shot, gray, cst.MATCH_PATH + 'report_manager/' +
                                                 cst.MATCH_IMG_RM[key], (0, 0, 255))

                # エキスパート設定のマッチングが失敗の場合、エラー終了
                if self.pos_xy['レポート'][0] is None or self.pos_xy['保存'][0] is None:
                    com.log('マッチングエラー: ' + str(self.pos_xy))
                    com.dialog('マッチングエラー\n　' + "\n　".join([key + ' = ' + str(self.pos_xy[key])
                                                           for key in self.pos_xy]), self.myjob, 'E')
                    return

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

                        # フォルダ内、全選択タイプ
                        if key.lower() == target_ea \
                                or (key.lower() != target_ea and i == len(targets) - 1):

                            self._call_report(ea_fold, targets[i], key.lower() == target_ea, True)
                            if key.lower() == target_ea:
                                break

                        # フォルダ内、個別指定タイプ
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
                self._select_report(ea_fold)
                wait = 40
            else:
                for cur in cst.CURRNCYS_EA[0]:
                    self._select_report(ea_fold + cur)
                    wait = 60
        else:
            if is_other:
                return

            for cur in cst.CURRNCYS_EA[0]:
                self._select_report(ea_fold + cur, "".join([file for file in target if 0 <= file.find(cur.lower())]))
                wait = 20

        self._save_report(('all' if is_all and not is_other else target[0].split('_')[0]), wait)

    def _select_report(self, path, file=None):

        # ダイヤログを開く
        pgui.hotkey('ctrl', 'o')
        com.sleep(2)

        # フォルダ選択
        com.clip_copy((TEST_PATH + path).replace('/', '\\'), True)
        com.sleep(2)

        # 全結合の場合は全選択
        if file is None:
            pgui.hotkey('ctrl', 'a')
            pgui.hotkey('enter')

        # 個別の場合は、ファイル指定
        else:
            com.clip_copy(file, True)

        com.sleep(1)

    def _save_report(self, file, wait):

        # マージファイル待機
        com.click_pos(self.pos_xy['保存'][0] + 5, self.pos_xy['保存'][1] + 5)
        com.sleep(3)
        pgui.hotkey('end')
        com.sleep(wait)

        # ダイヤログを開く
        com.click_pos(self.pos_xy['保存'][0] + 5, self.pos_xy['保存'][1] + 20)
        pgui.hotkey('ctrl', 'o')
        com.sleep(5)

        # フォルダ選択
        com.clip_copy((TEST_PATH + 'merge').replace('/', '\\'), True)
        com.sleep(2)
        com.clip_copy(file + '.htm', True)
        com.sleep(1)

        com.click_pos(self.pos_xy['レポート'][0] + 5, self.pos_xy['レポート'][1] + 5)
        com.log('保存完了: ' + TEST_PATH + 'merge/' + file + '.htm')


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
