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
            self.copy_history()

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

    def copy_history(self):
        if cst.IP == cst.DEV_IP:

            mt4_path = cst.CURRENT_PATH['Win'] + 'Documents/MT4/'
            in_path = ['DEV/OANDA', 'DEV/OANDA', 'DEV/OANDA', 'DEV/OANDA', 'TEST/Test2', 'RATE/MyFx']
            out_path = ['Test1', 'Test1_2', 'Test1_3', 'Test1_4', 'Test2_2', 'Test3']
            hst_name = ['Demo', 'Demo', 'Demo', 'Demo', 'Demo', 'Live']

            is_interrupt = False
            total_time = 0
            try:
                start_time = com.time_start()
                for i in range(0, len(in_path)):
                    hst_paths = os.listdir(mt4_path + in_path[i] + '/history')

                    # 進捗表示
                    bar = in_path[i] + '(' + str(i) + ' / ' + str(len(in_path)) + ')'
                    window = com.progress('ヒストリカルデータコピー中', [bar, len(in_path)])
                    event, values = window.read(timeout=0)

                    for hst_path in hst_paths:
                        if 0 <= hst_path.find(hst_name[i]):
                            break

                    files = os.listdir(cst.MT4_DEV + in_path[i] + '/history' + hst_path)
                    for file in files:
                        if file.find('.hst') < 0:
                            continue

                        shutil.copy2(cst.MT4_DEV + in_path[i] + '/history' + hst_path + file,
                                     cst.MT4_DEV + 'MT4_TEST/' + out_path[i] + '/history' + hst_path)
                        com.log('コピー完了: ' + cst.MT4_DEV.replace(cst.CURRENT_PATH['Win'] + '/', '') +
                                in_path[i] + '/history' + hst_path + file + ' → ' +
                                cst.MT4_DEV.replace(cst.CURRENT_PATH['Win'] + '/', '') +
                                'MT4_TEST/' + out_path[i] + '/history' + hst_path)

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
                com.log('コピー完了: ' + in_path[i] + ' → ' + out_path[i] + '(' + com.conv_time_str(run_time) + ')')

            finally:
                try: window.close()
                except: pass

            com.log(self.myjob + ': ' + ('中断' if is_interrupt else '全終了') + '(' + com.conv_time_str(total_time) + ')')
            com.dialog(('中断' if is_interrupt else '完了') + 'しました。(' + com.conv_time_str(total_time) + ')', self.myjob)

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