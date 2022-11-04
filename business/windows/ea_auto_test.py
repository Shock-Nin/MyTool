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
        self.start_ym = 0

    def do(self):

        prm_lists = inheritance.prm_list()
        prm_lists = [[prm_lists[0][1][i].replace('.set', '') for i in range(0, len(prm_lists[0][1]))],
                     [prm_lists[1][1][i].replace('.set', '') for i in range(0, len(prm_lists[1][1]))]]
        checks = com.dialog_cols('不要なものは外してください。', prm_lists, ['l' for _ in range(0, len(prm_lists))],
                                 'EA・通貨選択', obj='check')
        if 0 == len(checks):
            return

        inputs = com.input_box('開始年を選択してください。', '開始年設定',
                               [['開始年', 2007, int(com.str_time()[:4])]], obj='spin')
        if inputs[0] <= 0:
            return
        self.start_ym = inputs[1][0]

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
                                      [checks[i][0], len(checks[i])], interrupt=True)

                event, values = window.read(timeout=0)
                window[checks[i][0] + '_'].update(0)

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
                    if not self._set_mt4start(i, checks[i][k].split('_')[1]):
                        is_interrupt = True
                        break

                    if not is_start:

                        # エキスパート選択するまでクリック
                        shot, gray = com.shot_grab()
                        xy = [None, None]

                        while xy[0] is None:
                            xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['読み込み'], (0, 255, 0))

                            if xy[0] is None:
                                com.click_pos(self.pos_xy['エキスパート'][0] + 5, self.pos_xy['エキスパート'][1] + 5)
                                com.sleep(2)
                                shot, gray = com.shot_grab()
                            else:
                                break
                        # for m in range(1, 3):
                        #     com.click_pos(self.pos_xy['エキスパート'][0] + 5, self.pos_xy['エキスパート'][1] + (m * 5))
                        # com.sleep(3)
                        #
                        # # 全体画面の撮影
                        # shot, gray = com.shot_grab()
                        # if shot is None:
                        #     return

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
                        com.sleep(1)
                        pgui.hotkey('esc')

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

                            if not self._set_expert(path, file,
                                                    [logic, (prms[ea_name][0] if 'Best' == logic else '100')]):
                                is_interrupt = True
                                break

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

                        if not self._set_expert(path, file):
                            is_interrupt = True
                            break

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
    def _set_mt4start(self, ea_count, currency, time_frame='H1', end_ym=str(int(com.str_time()[:4]) + 1) + '.01'):

        try:
            # EA選択
            for i in range(1, 3):
                com.click_pos(self.pos_xy['エキスパート'][0] - 200, self.pos_xy['エキスパート'][1] + (5 * i))
                com.sleep(1)
                [pgui.hotkey('up') for _ in range(10)]
                [pgui.hotkey('down') for _ in range(0, ea_count)]
                pgui.hotkey('enter')
            com.sleep(2)

            # 開始日～終了日
            for i in range(1, 3):
                com.click_pos(self.pos_xy['開始日'][0] + 60, self.pos_xy['開始日'][1] + (5 * i))
                pgui.write(self.start_ym)
                pgui.hotkey('right')
                pgui.write('01')
                com.sleep(2)
                com.click_pos(self.pos_xy['終了日'][0] + 60, self.pos_xy['終了日'][1] + (5 * i))
                pgui.write(end_ym[:4])
                pgui.hotkey('right')
                pgui.write(end_ym[5:])
                com.sleep(2)

            # 通貨ペア
            for i in range(1, 3):
                com.click_pos(self.pos_xy['通貨'][0] + 100, self.pos_xy['通貨'][1] + (5 * i))
                com.sleep(1)
                pgui.hotkey('home')
                [pgui.hotkey('down') for _ in range(0, cst.CURRNCYS_EA[0].index(currency))]
                pgui.hotkey('enter')
            com.sleep(2)

            # スプレッド
            spread = "".join([cst.CURRNCYS_EA[1][n] for n in range(0, len(cst.CURRNCYS_EA[0]))
                              if currency == cst.CURRNCYS_EA[0][n]])

            for i in range(1, 3):
                com.click_pos(self.pos_xy['スプレッド'][0] + 100, self.pos_xy['スプレッド'][1] + 25 + (5 * i))
                [pgui.hotkey('backspace') for _ in range(0, 5)]
                pgui.write(spread)
            com.sleep(1)

            # 期間
            for i in range(1, 3):
                com.click_pos(self.pos_xy['スプレッド'][0] + 100, self.pos_xy['スプレッド'][1] + (5 * i))
                pgui.hotkey('home')
                [pgui.hotkey('down') for _ in range(0, ['M1', 'M5', 'M15', 'M30', 'H1', 'H4'].index(time_frame))]
                pgui.hotkey('enter')
            com.sleep(2)

            # 最適化外し
            if self.pos_xy['最適化ON'][0] is not None:
                com.click_pos(self.pos_xy['最適化ON'][0] + 5, self.pos_xy['最適化ON'][1] + 5)
                com.sleep(2)

            com.log('MT4設定: ' + currency + '(' + cst.EA_START_YM + ' 〜 ' + end_ym + ') 時間足 ' + time_frame + ', スプレッド ' + spread)
        except Exception as e:
            com.log('MT4初期設定エラー: ' + str(e), 'E')
            com.dialog('MT4初期設定で、エラーが発生しました。\n' + str(e), 'エラー発生', 'E')
            return False

        return True

    # パラメータの設定
    def _set_expert(self, path, file, prm=None):
        try:
            target = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH + path + '/' + file + '.set'

            # エキスパート選択するまでクリック
            shot, gray = com.shot_grab()
            xy = [None, None]

            while xy[0] is None:
                xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['読み込み'], (0, 255, 0))

                if xy[0] is None:
                    com.click_pos(self.pos_xy['エキスパート'][0] + 5, self.pos_xy['エキスパート'][1] + 5)
                    com.sleep(2)
                    shot, gray = com.shot_grab()
                else:
                    break

            com.sleep(3)
            pgui.hotkey('alt', 'l')
            com.sleep(5)

            com.clip_copy(target.replace('/', '\\'), True)
            com.sleep(5)

            # パラメータの変更がある場合
            if prm is not None:

                # Logics選択するまでクリックして入力
                if prm[0] not in ['Best', 'Full']:
                    shot, gray = com.shot_grab()
                    xy = [None, None]

                    while xy[0] is None:
                        xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['Logics選択'], (0, 255, 0))

                        if xy[0] is None:
                            com.click_pos(self.pos_xy['値'][0] - 70, self.pos_xy['Logics'][1] + 5, click=2)
                            com.sleep(2)
                            shot, gray = com.shot_grab()
                        else:
                            com.clip_copy(prm[0], True)
                            com.sleep(2)
                            break

                # Risk選択するまでクリックして入力
                shot, gray = com.shot_grab()
                xy = [None, None]

                while xy[0] is None:
                    xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['Risk選択'], (0, 255, 0))

                    if xy[0] is None:
                        com.click_pos(self.pos_xy['値'][0] - 70, self.pos_xy['Risk'][1] + 5, click=2)
                        com.sleep(2)
                        shot, gray = com.shot_grab()
                    else:
                        com.clip_copy(prm[1], True)
                        com.sleep(2)
                        break

            [pgui.hotkey('tab') for _ in range(0, 3)]
            pgui.hotkey('enter')
            com.sleep(3)

            com.log('テスト開始: ' + target + ', ' + str(prm))

            # ストップに変化するまでスタートボタン押下
            shot, gray = com.shot_grab()
            xy = [None, None]

            while xy[0] is None:
                xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['ストップ'], (0, 255, 0))

                if xy[0] is None:
                    com.click_pos(self.pos_xy['スタート'][0] + 5, self.pos_xy['スタート'][1] + 5)
                    com.sleep(2)
                    shot, gray = com.shot_grab()
                else:
                    break

        except Exception as e:
            com.log('パラメータ設定エラー: ' + str(e), 'E')
            com.dialog('パラメータ設定で、エラーが発生しました。\n' + str(e), 'エラー発生', 'E')
            return False

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
                xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4['スタート'], (0, 255, 0))

                # MT4閉じた場合の中断
                if xy[0] is None \
                        and self._get_position(shot, gray, cst.MATCH_IMG_MT4['ストップ'], (0, 255, 0))[0] is None:
                    is_interrupt = True
                    break

        except Exception as e:
            com.log('テスト保存エラー: ' + str(e), 'E')
            com.dialog('テスト保存で、エラーが発生しました。\n' + str(e), 'エラー発生', 'E')
            return False

        finally:
            # マッチングのマーキングimg出力
            try: cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)
            except: pass

        if is_interrupt:
            return False

        try:
            com.sleep(3)
            target = cst.TEST_UNIT[cst.PC] + path + '/' + file + '.htm'

            # 全体画面の撮影
            shot, gray = com.shot_grab()

            # レポート保存
            report = self._get_position(shot, gray, cst.MATCH_IMG_MT4['レポート'], (0, 255, 0))

            if report[0] is None:
                com.log('レポートマッチングエラー: ' + file, 'E')
                com.dialog('レポートマッチングエラーが発生しました。\n' + file, 'エラー発生', 'E')
                return False
            else:

                for i in range(1, 3):
                    com.click_pos(report[0] + 5, report[1] + (i * 5))
                    com.sleep(2)

                pgui.rightClick(report[0] - 100, report[1] - 100)
                com.sleep(1)
                pgui.rightClick(report[0] + 100, report[1] - 100)
                com.sleep(1)
                pgui.hotkey('s')
                com.sleep(3)
                com.clip_copy(target.replace('/', '\\'), True)
                com.sleep(1)
                pgui.hotkey('y')
                com.sleep(3)

                for i in range(1, 3):
                    com.click_pos(40, report[1] + (i * 5))
                    com.sleep(2)

                # マッチングのマーキングimg出力
                cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)
                com.log('テストデータ保存: ' + target)

        except Exception as e:
            com.log('テスト保存エラー: ' + str(e), 'E')
            com.dialog('テスト保存で、エラーが発生しました。\n' + str(e), 'エラー発生', 'E')
            return False

        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
