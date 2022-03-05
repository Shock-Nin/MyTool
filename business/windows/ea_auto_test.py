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

PRM_PATH = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH
EA_EXE = cst.MT4_DEV[cst.PC] + '/terminal.exe /portable'


class EaAutoTest:

    def __init__(self, job):
        self.myjob = job
        self.pos_xy = cst.MATCH_IMG_MT4.copy()

    def do(self):

        prm_lists = inheritance.prm_list()
        prm_lists = [[prm_lists[0][1][i].replace('.set', '') for i in range(0, len(prm_lists[0][1]))],
                     [prm_lists[1][1][i].replace('.set', '') for i in range(0, len(prm_lists[1][1]))]]
        checks = com.dialog_cols('不要なものは外してください。', prm_lists, ['l' for _ in range(0, len(prm_lists))],
                                 'EA・通貨選択', obj='check')
        if 0 == len(checks):
            return

        # パラメータ読み込み
        check_logics = []
        read_files = []
        prms = {}
        err_msg = ''
        if 0 < len(checks[-1]):
            for i in range(1, len(checks)):
                for k in range(0, len(checks[i])):

                    ea_name = checks[i][k].split('_')[0]
                    if len(checks) - 1 == i:
                        try:
                            read_files.append(open(PRM_PATH + cst.EA_PATHS[ea_name][0] + '/' +
                                                   checks[i][k] + '.set', 'r').read())

                        except Exception as e:
                            err_msg += '\n　' + checks[i][k] + '.set' + '\n　　' + str(e)
                            com.log(str(e))

            # 読み込んだ対象ファイルの整形
            for file in read_files:

                datas = file.split('\n')
                ea_name = ''
                risk = ''
                logic = 0
                logics = []

                for data in datas:

                    if 0 <= data.find(',') or 0 <= data.find('_____'):
                        continue
                    vals = data.split('=')

                    try:
                        if 'Comments' == vals[0]:
                            ea_name = vals[1]
                        if 'Risk' == vals[0]:
                            risk = vals[1]
                        if 0 <= vals[0].find('Lot'):
                            logic += 1
                            logics.append(('0' if logic < 10 else '') + str(logic))
                    except:
                        pass

                logics.append('Full')
                logics.append('Best')
                prms[ea_name] = [risk, logics]

            check_logics = com.dialog_cols(ea_name.split('_')[0] + '\n不要なものは外してください。',
                                           [prms[ea_name][1]], ['l' for _ in range(0, len(prms[ea_name]))],
                                           ea_name.split('_')[0] + 'ロジック選択', obj='check')
            if 0 == len(check_logics):
                return

        total_time = 0

        # 進捗と中断の監視
        is_interrupt = False
        try:
            for i in range(0, len(checks)):
                if 0 == len(checks[i]):
                    continue

                is_start = False

                window = com.progress(self.myjob + '(' + com.str_time().split(' ')[1] + ')',
                                      [checks[i][0].split('_')[0], len(checks)],
                                      [checks[i][0], len(checks[0])], interrupt=True)

                event, values = window.read(timeout=0)

                for k in range(0, len(checks[i])):
                    mt4_start = com.time_start()

                    window[checks[i][0].split('_')[0]].update(checks[i][k].split('_')[0] +
                                                              '(' + str(i) + '/' + str(len(checks)) + ')')
                    window[checks[i][0]].update(checks[i][k] + '(' + str(k) + '/' + str(len(checks[i])) + ')')
                    window[checks[i][0].split('_')[0] + '_'].update(i)
                    window[checks[i][0] + '_'].update(k)

                    # MT4起動
                    if 'Win' == cst.PC:
                        process = subprocess.Popen(EA_EXE)
                        com.sleep(cst.MT4_WAIT[0])
                        process.kill()
                        com.sleep(2)
                        process = subprocess.Popen(EA_EXE)

                    com.sleep(cst.MT4_WAIT[1])

                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                    # MT4初回起動は、テンプレートマッチング
                    if not is_start:
                        com.log('初回マッチング開始')

                        # 全体画面の撮影
                        shot, gray = com.shot_grab()
                        if shot is None:
                            return

                        for key in cst.MATCH_IMG_MT4:
                            self.pos_xy[key] = self._get_position(shot, gray, cst.MATCH_IMG_MT4[key], (0, 0, 255))

                        # エキスパート設定のマッチングが失敗の場合、エラー終了
                        if self.pos_xy['エキスパート'][0] is None:
                            com.log('初回マッチングエラー: ' + str(self.pos_xy))
                            com.dialog('初回マッチングエラー\n　' + "\n　".join([key + ' = ' + str(self.pos_xy[key])
                                                                     for key in self.pos_xy]), self.myjob, 'E')
                            return

                    # MT4起動時設定
                    self._set_mt4start(i, checks[i][k].split('_')[1])

                    if not is_start:
                        com.click_pos(self.pos_xy['エキスパート'][0] + 5, self.pos_xy['エキスパート'][1] + 5)
                        com.sleep(3)

                        # 全体画面の撮影
                        shot, gray = com.shot_grab()
                        if shot is None:
                            return

                        com.sleep(3)
                        for key in cst.MATCH_IMG_MT4:

                            if self.pos_xy[key][0] is None:
                                xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4[key], (255, 0, 0))

                                if xy[0] is not None:
                                    self.pos_xy[key] = xy

                        # 読み込みのマッチングが失敗の場合、エラー終了
                        if self.pos_xy['読み込み'][0] is None:
                            com.log('初回マッチングエラー: ' + str(self.pos_xy))
                            com.dialog('初回マッチングエラー\n　' + "\n　".join([key + ' = ' + str(self.pos_xy[key])
                                                                     for key in self.pos_xy]), self.myjob, 'E')
                            return

                        # 何もせずに閉じる
                        com.click_pos(self.pos_xy['読み込み'][0] + 5, self.pos_xy['読み込み'][1] + 40)

                        # マッチングのマーキングimg出力
                        cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)
                        com.log('初回マッチング完了: ' + str(self.pos_xy))

                        is_start = True

                    mt4_run = com.time_end(mt4_start)
                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                    # パラメータ内のロジック実行
                    if len(checks) - 1 == i:
                        ea_name = checks[i][k]
                        cur = ea_name.split('_')[1]

                        for logic in prms[ea_name][1]:
                            if logic not in check_logics[0]:
                                continue

                            # 中断イベント
                            if _is_interrupt(window, event):
                                is_interrupt = True
                                break

                            start_time = com.time_start()
                            com.sleep(5)

                            path = cst.EA_PATHS[ea_name.split('_')[0]][0]
                            file = ea_name

                            com.log('テスト開始: ' + ea_name + ', ' + logic)

                            self._set_expert(path, file, [logic, (prms[ea_name][0] if 'Best' == logic else '100')])

                            path = cst.EA_PATHS[ea_name.split('_')[0]][-1] + cur
                            file = logic + '_' + cur

                            if not self._save_report(path, file, window, event):
                                is_interrupt = True
                                break

                            run_time = com.time_end(start_time) + (mt4_run / len(check_logics[0]))
                            total_time += run_time
                            com.log('テスト終了(' + com.conv_time_str(run_time) + '): ' + ea_name + ', ' + logic)

                            # 中断イベント
                            if _is_interrupt(window, event):
                                is_interrupt = True
                                break
                    else:
                        # 中断イベント
                        if _is_interrupt(window, event):
                            is_interrupt = True
                            break

                        start_time = com.time_start()
                        com.sleep(5)

                        path = cst.EA_PATHS[checks[i][k].split('_')[0]][-1]
                        file = checks[i][k]
                        com.log('テスト開始: ' + file)

                        self._set_expert(path, file)

                        if not self._save_report(path, checks[i][k], window, event):
                            is_interrupt = True
                            break

                        run_time = com.time_end(start_time) + mt4_run
                        total_time += run_time
                        com.log('テスト終了(' + com.conv_time_str(run_time) + '): ' + file)

                        # 中断イベント
                        if _is_interrupt(window, event):
                            is_interrupt = True
                            break

                    # 中断送り
                    if is_interrupt:
                        break

                    # MT4クローズとヒストリカル削除
                    if 'Win' == cst.PC:
                        process.kill()
                        [os.remove(cst.MT4_DEV[cst.PC] + 'tester/history/' + fxt)
                         for fxt in os.listdir(cst.MT4_DEV[cst.PC] + 'tester/history')]

                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                window.close()

                # 中断送り
                if is_interrupt:
                    break
        finally:
            try: window.close()
            except: pass
            try: process.kill()
            except: pass

        com.log(self.myjob + ': ' + ('中断' if is_interrupt else '全終了') + '(' + com.conv_time_str(total_time) + ')')
        com.dialog(('中断' if is_interrupt else '完了') + 'しました。(' + com.conv_time_str(total_time) + ')', self.myjob)
        return

    # テンプレートマッチング
    def _get_position(self, shot, gray, img, color=(255, 0, 255)):
        x, y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' + img, color)
        return [x, y]

    # MT4起動時の設定
    def _set_mt4start(self, ea_count, currency, time_frame='H1', start_ym='2005.01', end_ym=com.str_time()[:4] + '.01'):

        # EA選択
        com.click_pos(self.pos_xy['エキスパート'][0] - 100, self.pos_xy['エキスパート'][1] + 5)
        pgui.hotkey('home')
        [pgui.hotkey('down') for _ in range(0, ea_count)]
        pgui.hotkey('enter')

        # 開始日～終了日
        com.click_pos(self.pos_xy['開始日'][0] + 50, self.pos_xy['開始日'][1] + 5)
        pgui.write(start_ym[:4])
        pgui.hotkey('right')
        pgui.write(start_ym[5:])
        com.click_pos(self.pos_xy['終了日'][0] + 50, self.pos_xy['終了日'][1] + 5)
        pgui.write(end_ym[:4])
        pgui.hotkey('right')
        pgui.write(end_ym[5:])

        # 通貨ペア
        com.click_pos(self.pos_xy['通貨'][0] + 70, self.pos_xy['通貨'][1] + 5)
        pgui.hotkey('home')
        [pgui.hotkey('down') for _ in range(0, cst.CURRNCYS_EA[0].index(currency))]
        pgui.hotkey('enter')

        # スプレッド
        spread = "".join([cst.CURRNCYS_EA[1][n] for n in range(0, len(cst.CURRNCYS_EA[0]))
                          if currency == cst.CURRNCYS_EA[0][n]])
        com.click_pos(self.pos_xy['スプレッド'][0] + 100, self.pos_xy['スプレッド'][1] + 30)
        pgui.write(spread)

        # 期間
        com.click_pos(self.pos_xy['スプレッド'][0] + 100, self.pos_xy['スプレッド'][1] + 5)
        pgui.hotkey('home')
        [pgui.hotkey('down') for _ in range(0, ['M1', 'M5', 'M15', 'M30', 'H1', 'H4'].index(time_frame))]
        pgui.hotkey('enter')

        # 最適化外し
        if self.pos_xy['最適化ON'][0] is not None:
            com.click_pos(self.pos_xy['最適化ON'][0] + 5, self.pos_xy['最適化ON'][1] + 5)

        print('MT4設定: ' + currency + '(' + start_ym + ' 〜 ' + end_ym + ') 時間足 ' + time_frame + ', スプレッド ' + spread)
        return True

    # パラメータの設定
    def _set_expert(self, path, file, prm=None):

        target = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH + path + '/' + file + '.set'

        com.click_pos(self.pos_xy['エキスパート'][0] + 5, self.pos_xy['エキスパート'][1] + 5)
        com.sleep(3)
        com.click_pos(self.pos_xy['読み込み'][0] + 5, self.pos_xy['読み込み'][1] + 5)
        com.sleep(3)

        com.clip_copy(target.replace('/', '\\'), True)

        # パラメータの変更がある場合
        if prm is not None:

            com.sleep(3)
            if prm[0] not in ['Best', 'Full']:
                com.click_pos(self.pos_xy['値'][0] - 70, self.pos_xy['Logics'][1] + 5, dbl=True)
                com.clip_copy(prm[0], True)
                com.sleep(1)

            com.click_pos(self.pos_xy['値'][0] - 70, self.pos_xy['Risk'][1] + 5, dbl=True)
            com.clip_copy(prm[1], True)
            com.sleep(1)

        com.click_pos(self.pos_xy['読み込み'][0] + 5, self.pos_xy['読み込み'][1] + 40)
        com.sleep(3)

        print('テスト開始: ' + target + ', ' + str(prm))
        com.click_pos(self.pos_xy['スタート'][0] + 5, self.pos_xy['スタート'][1] + 5)

        return True

    # テストの保存
    def _save_report(self, path, file, window, event):

        com.sleep(10)
        xy = [None, None]
        is_interrupt = False

        try:
            # テストが終了して、ストップがスタートに切り替わるまで待機
            while xy[0] is None:
                com.sleep(5)

                # 中断イベント
                if _is_interrupt(window, event):
                    is_interrupt = True
                    break

                # 全体画面の撮影
                shot, gray = com.shot_grab()
                if shot is None:
                    break

                xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['スタート'], (0, 255, 0))

                # MT4閉じた場合の中断
                if xy[0] is None \
                        and self._get_position(shot, gray, cst.MATCH_IMG_MT4['ストップ'], (0, 255, 0))[0] is None:
                    is_interrupt = True
                    break

        finally:
            # マッチングのマーキングimg出力
            try: cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)
            except: pass

        if is_interrupt:
            return False

        com.sleep(3)
        target = cst.TEST_UNIT[cst.PC] + path + '/' + file + '.htm'

        # 全体画面の撮影
        shot, gray = com.shot_grab()
        if shot is None:
            return False

        # レポート保存
        report = self._get_position(shot, gray, cst.MATCH_IMG_MT4['レポート'], (0, 255, 0))

        com.click_pos(report[0] + 5, report[1] + 5)
        com.sleep(2)
        pgui.rightClick(report[0] + 5, report[1] - 100)
        com.sleep(1)
        pgui.hotkey('s')
        com.sleep(3)
        com.clip_copy(target.replace('/', '\\'), True)
        com.sleep(1)
        pgui.hotkey('y')
        com.sleep(3)
        com.click_pos(30, report[1] + 5)

        # マッチングのマーキングimg出力
        cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)
        print('テストデータ保存: ' + target)
        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
