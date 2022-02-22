#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import cv2
import subprocess
import PySimpleGUI as sg
from PIL import ImageGrab

from business. windows import ea_edits as inheritance

PRM_PATH = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH
EA_EXE = cst.MT4_DEV[cst.PC] + '/terminal.exe /portable'


class EaAutoTest:

    def __init__(self, job):
        self.myjob = job
        self.pos_xy = cst.MATCH_IMG_MT4

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
        while True:
            for i in range(0, len(checks)):
                window = com.progress(self.myjob,
                                      [checks[i][0].split('_')[0], len(checks)],
                                      [checks[i][0], len(checks[0])], interrupt=True)
                if 'Win' == cst.PC:
                    event, values = window.read()
                else:
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
                    self._set_mt4start(spread=("".join([cst.CURRNCYS_EA[1][n] for n in range(0, len(cst.CURRNCYS_EA[0]))
                                               if checks[i][k].split('_')[1] == cst.CURRNCYS_EA[0][n]])))

                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                    # MT4初回起動は、テンプレートマッチング
                    if 0 == i + k:
                        com.log('初回マッチング開始')

                        # 全体画面の撮影
                        shot_path = cst.TEMP_PATH[cst.PC] + 'shot.png'
                        ImageGrab.grab().save(shot_path)
                        shot = cv2.imread(shot_path)
                        gray = cv2.imread(shot_path, 0)

                        for key in cst.MATCH_IMG_MT4:
                            self.pos_xy[key] = self._get_position(shot, gray, cst.MATCH_IMG_MT4[key])

                        # MT4初回起動は、エキスパート設定のマッチング
                        if 0 == i + k:
                            if self.pos_xy['エキスパート'][0] is not None:
                                com.click_pos(self.pos_xy['エキスパート'][0] / 2, self.pos_xy['エキスパート'][1] / 2)
                                com.sleep(3)

                                for key in cst.MATCH_IMG_MT4:
                                    xy = self._get_position(shot, gray, cst.MATCH_IMG_MT4[key])
                                    if xy[0] is None:
                                        self.pos_xy[key] = xy

                                # 何もせずに閉じる
                                com.click_pos(self.pos_xy['エキスパート'][0] / 2, self.pos_xy['エキスパート'][1] / 2)

                        com.log('初回マッチング完了: ' + str(self.pos_xy))

                    mt4_run = com.time_end(mt4_start)

                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                    # パラメータ内のロジック実行
                    if len(checks) - 1 == i:
                        ea_name = checks[i][k]

                        for logic in prms[ea_name][1]:
                            if logic not in check_logics[0]:
                                continue

                            # 中断
                            if _is_interrupt(window, event):
                                is_interrupt = True
                                break

                            start_time = com.time_start()
                            com.sleep(5)

                            cur = ea_name.split('_')[1]
                            path = cst.EA_PATHS[ea_name.split('_')[0]][0] + cur
                            file = ea_name

                            com.log('テスト開始: ' + ea_name + ', ' + logic)

                            self._set_expert(path, file, [logic, (prms[ea_name][0] if 'Best' == logic else '100')])

                            path = cst.EA_PATHS[ea_name.split('_')[0]][-1] + cur
                            file = logic + '_' + cur
                            self._save_report(path, file)

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

                        self._save_report(path, checks[i][k])

                        run_time = com.time_end(start_time) + mt4_run
                        total_time += run_time
                        com.log('テスト終了(' + com.conv_time_str(run_time) + '): ' + file)

                        # 中断イベント
                        if _is_interrupt(window, event):
                            is_interrupt = True
                            break

                    # MT4クローズ
                    if 'Win' == cst.PC:
                        process.kill()

                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                window.close()

                # 中断送り
                if is_interrupt:
                    break
            break

        com.log(self.myjob + ': 全終了(' + com.conv_time_str(total_time) + ')')
        com.dialog('完了しました。(' + com.conv_time_str(total_time) + ')', self.myjob)
        return

    # テンプレートマッチング
    def _get_position(self, shot, gray, img):
        x, y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' + img, (255, 0, 255))
        return [x, y]

    # MT4起動時の設定
    def _set_mt4start(self, time_frame='H1', spread='25', start_ym='2005.01', end_ym=com.str_time()[:4] + '.01'):

        print('MT4設定: ' + start_ym + ' 〜 ' + end_ym + ', 時間足 ' + time_frame + ', スプレッド ' + spread)
        return True

    # パラメータの設定
    def _set_expert(self, path, file, prm=None):

        if self.pos_xy['エキスパート'][0] is None:
            return False

        target = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH + path + '/' + file + '.set'

        com.click_pos(self.pos_xy['エキスパート'][0] / 2, self.pos_xy['エキスパート'][1] / 2)
        com.sleep(3)

        print('パラメータ呼び出し: ' + target + ', ' + str(prm))
        return True

    # テストの保存
    def _save_report(self, path, file):
        target = cst.TEST_UNIT[cst.PC] + path + '/' + file + '.htm'

        print('テストデータ保存: ' + target)
        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
