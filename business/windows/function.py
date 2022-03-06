#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import os
import shutil
import subprocess
import PySimpleGUI as sg


class Function:

    def __init__(self, job):
        self.myjob = job

    def do(self, fnc):

        if com.question(fnc + ' 開始しますか？', '開始確認') <= 0:
            return

        if fnc in ['最適化セット', '最適化MT4起動']:

            if '最適化セット' == fnc:
                pass

        elif 'EX4コピー' == fnc:
            if cst.IP == cst.DEV_IP:
                pass
            else:
                pass

        elif 'EX4展開' == fnc:
            pass

        elif 'ヒストリカル編集' == fnc:
            pass

        elif 'ヒストリカルコピー' == fnc:
            self.copy_history(fnc)

        else:
            target = ''
            if 'MQL編集' == fnc:
                target = cst.MT4_DEV['Win'] + 'metaeditor.exe /portable'
            elif 'Winアップデート' == fnc:
                target = os.getcwd() + '/item/app/Wub/Wub.exe'
            elif 'ヒストリカル取得' == fnc:
                target = cst.TICK_HISTORY[0]

            return subprocess.Popen(target)

    def set_optimize(self):
        pass

    def copy_history(self, fnc):
        if cst.IP == cst.DEV_IP:

            mt4_path = cst.CURRENT_PATH['Win'] + 'Documents/MT4/'
            in_path = ['MT4_DEV/OANDA', 'MT4_DEV/OANDA', 'MT4_DEV/OANDA', 'MT4_TEST/Test2', 'MT4_RATE/MyFx']
            out_path = ['Test1', 'Test1_2', 'Test1_3', 'Test2_2', 'Test3']
            hst_name = ['Demo', 'Demo', 'Demo', 'Demo', 'Live']

            is_interrupt = False
            total_time = 0
            try:
                for i in range(0, len(in_path)):

                    start_time = com.time_start()
                    hst_paths = os.listdir(mt4_path + in_path[i] + '/history')

                    # ヒストリカルデータの対象サーバー名を検索
                    for hst_path in hst_paths:
                        if 0 <= hst_path.find(hst_name[i]):
                            break

                    files = os.listdir(mt4_path + in_path[i] + '/history/' + hst_path)
                    files = [file for file in files if 0 <= file.find('.hst')]

                    # 進捗表示
                    bar1 = in_path[i] + ' → MT4_TEST/' + out_path[i]
                    bar2 = files[0]
                    window = com.progress('ヒストリカルデータコピー中',
                                          [bar1, len(in_path)], [bar2, len(files)], interrupt=True)
                    event, values = window.read(timeout=0)

                    for k in range(0, len(files)):

                        window[in_path[i] + ' → MT4_TEST/' + out_path[i]].update(
                            in_path[i] + ' → MT4_TEST/' + out_path[i] + '(' + str(i) + ' / ' + str(len(in_path)) + ')')
                        window[files[0]].update(files[k] + '(' + str(k) + ' / ' + str(len(files)) + ')')
                        window[in_path[i] + ' → MT4_TEST/' + out_path[i] + '_'].update(i)
                        window[files[0] + '_'].update(k)

                        shutil.copy2(mt4_path + in_path[i] + '/history/' + hst_path + '/' + files[k],
                                     mt4_path + 'MT4_TEST/' + out_path[i] + '/history/' + hst_path)
                        com.log('コピー中: ' + hst_path + '/' + files[k] + ' | ' +
                                in_path[i] + ' → ' + 'MT4_TEST/' + out_path[i])

                        # 中断イベント
                        if _is_interrupt(window, event):
                            is_interrupt = True
                            break

                    # 中断送り
                    if is_interrupt:
                        break
                    window.close()

                    run_time = com.time_end(start_time)
                    total_time += run_time
                    com.log('コピー完了(' + com.conv_time_str(run_time) + ')  [' + mt4_path[:-1] + '] ' +
                            in_path[i] + ' → MT4_TEST/' + out_path[i])

            finally:
                try: window.close()
                except: pass

            com.log(fnc+ ': ' + ('中断' if is_interrupt else '全終了') + '(' + com.conv_time_str(total_time) + ')')
            com.dialog(('中断' if is_interrupt else '完了') + 'しました。(' + com.conv_time_str(total_time) + ')', fnc)

        else:
            com.log('端末対象外: ' + cst.IPS[cst.IP])

        return True

    def edit_history(self):
        pass

    def open_mt4(self):
        pass


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False