#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import os
import cv2
import shutil
import subprocess
import PySimpleGUI as sg


class Function:

    def __init__(self, job):
        self.myjob = job

    def do(self, fnc):

        if com.question(fnc + ' 開始しますか？', '開始確認') <= 0:
            return

        if fnc in ['最適化セット', 'MT4起動']:
            self.set_optimize(
                fnc, opt_path=['MT4_DEV/OANDA', 'MT4_TEST/Test1', 'MT4_TEST/Test1-2', 'MT4_TEST/Test1-3'],
                affinity=['F', '2', '4', '8'],
                web_path=['Web_MT4'],
                my_path=['FxPro', 'OANDA', 'Rakuten']  # 'MyFx', 'XM'
            )
        elif 'EX4コピー' == fnc:
            self.copy_ex4(
                fnc, dev_out=['Test1', 'Test1-2', 'Test1-3', 'Test2', 'Test2_2', 'Test3'],
                web_path=['Web_MT4'],
                my_path=['FxPro', 'OANDA', 'Rakuten', 'MyFx', 'XM'],
                target_ea=['AnomalyShocknin', 'AnomalyGoToBe'],
                target_ind=['AnomalyShocknin*', 'AnomalyGoToBe', 'sts*', 'JikanDeGo', 'WheSitaDoch'],
                remove_ea=[],
                remove_ind=[]
            )
        elif 'ヒストリカル編集' == fnc:
            pass

        elif 'ヒストリカルコピー' == fnc:
            self.copy_history(
                fnc, in_path=['MT4_DEV/OANDA', 'MT4_DEV/OANDA', 'MT4_DEV/OANDA', 'MT4_TEST/Test2', 'MT4_RATE/MyFx'],
                out_path=['Test1', 'Test1_2', 'Test1_3', 'Test2_2', 'Test3'],
                hst_name=['Demo', 'Demo', 'Demo', 'Demo', 'Live']
            )
        else:
            target = ''
            if 'MQL編集' == fnc:
                target = cst.MT4_DEV['Win'] + 'metaeditor.exe /portable'
            elif 'Winアップデート' == fnc:
                target = os.getcwd() + '/item/app/Wub/Wub.exe'
            elif 'Tickstory' == fnc:
                target = cst.TICK_HISTORY[0]

            if 0 < len(target):
                return subprocess.Popen(target)

        return []

    # 最適化MT4起動と、set読み込み
    def set_optimize(self, fnc, opt_path, affinity, web_path, my_path):
        if 'Win' == cst.PC:

            # MT4起動コマンドを設定
            commands = []
            if cst.IP == cst.DEV_IP:
                for i in range(0, len(opt_path)):
                    commands.append('start "" /affinity ' + affinity[i] +
                                    ' "' + cst.MT4_PATH + opt_path[i] + '/terminal.exe" "/portable"')
            elif cst.IP == cst.WEB_IP:
                for i in range(0, len(web_path)):
                    commands.append(cst.MT4_PATH + web_path[i] + '/terminal.exe /portable')

            elif cst.IP == cst.MY_IP:
                for i in range(0, len(my_path)):
                    commands.append(cst.MT4_PATH + my_path[i] + '/terminal.exe /portable')

            # 全体画面の撮影
            shot, gray = com.shot_grab()
            if shot is None:
                return False

            # MT4が開かれていない場合、MT4を起動
            expert_x, expert_y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' +
                                           cst.MATCH_IMG_MT4['エキスパート'], (0, 0, 255))
            if expert_x is not None:
                for i in range(0, len(commands)):
                    subprocess.Popen(commands[i])
                    com.sleep(1)
            else:
                com.log(fnc + ': MT4起動済み')

            if '最適化セット' == fnc:
                com.sleep(3)

                # 全体画面の撮影
                shot, gray = com.shot_grab()
                if shot is None:
                    return False

                # エキスパート設定のマッチングが失敗の場合、エラー終了
                expert_x, expert_y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' +
                                               cst.MATCH_IMG_MT4['エキスパート'], (0, 0, 255))
                if expert_x is None:
                    return False

                for i in range(1, len(commands)):
                    subprocess.Popen(commands[i])
                    com.sleep(3)

                    com.click_pos(expert_x + 5, expert_y + 5)
                    com.sleep(2)

                    # 全体画面の撮影
                    shot, gray = com.shot_grab()

                    # 読み込みボタン
                    read_x, read_y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' +
                                               cst.MATCH_IMG_MT4['読み込み'], (0, 255, 255))
                    # 最適化チェック
                    opt_x, opt_y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' +
                                             cst.MATCH_IMG_MT4['最適化OFF'], (255, 0, 255))

                    com.click_pos(read_x + 5, read_y + 5)
                    com.sleep(2)

                    com.clip_copy((cst.GDRIVE_PATH['Win'] + 'FX/Presets/開発用.set').replace('/', '\\'), True)
                    com.sleep(2)

                    # 最適化チェック
                    if opt_x is not None:
                        com.click_pos(opt_x + 5, opt_y + 5)

                # マッチングのマーキングimg出力
                cv2.imwrite(cst.TEMP_PATH[cst.PC] + 'out.png', shot)
                com.log(fnc + ': 最適化セット')
        else:
            com.log(fnc + ': 端末対象外 ' + cst.IPS[cst.IP])

        return True

    # EAとインジケータのコピー
    def copy_ex4(self, fnc, dev_out, web_path, my_path, target_ea, target_ind, remove_ea, remove_ind):
        if 'Win' == cst.PC:
            center = cst.GDRIVE_PATH['Win'] + 'FX/MQL4/'

            if cst.IP == cst.DEV_IP:
                in_path = cst.MT4_PATH + 'MT4_DEV/OANDA/MQL4/'

                for out in dev_out:
                    out_path = cst.MT4_PATH + 'MT4_TEST/' + out + '/MQL4/'

                    for target in target_ea:
                        # shutil.copy2(in_path + 'Experts' + target + 'ex4', out_path + 'Experts')
                        # shutil.copy2(in_path + 'Experts' + target + 'ex4', center + 'Experts')
                        com.log('コピー: ' + in_path + 'Experts' + target + 'ex4' + ' → ' + out_path + 'Experts')
                        com.log('コピー: ' + in_path + 'Experts' + target + 'ex4' + ' → ' + center + 'Experts')
                    for target in target_ind:
                        # shutil.copy2(in_path + 'Indicators' + target + 'ex4', out_path + 'Indicators')
                        # shutil.copy2(in_path + 'Indicators' + target + 'ex4', center + 'Indicators')
                        com.log('コピー: ' + in_path + 'Indicators' + target + 'ex4' + ' → ' + out_path + 'Indicators')
                        com.log('コピー: ' + in_path + 'Indicators' + target + 'ex4' + ' → ' + center + 'Indicators')

                    for target in remove_ea:
                        # os.remove(out_path + 'Experts' + target + 'ex4')
                        # os.remove(center + 'Experts' + target + 'ex4')
                        com.log('削除: ' + out_path + 'Experts' + target + 'ex4')
                        com.log('削除: ' + center + 'Experts' + target + 'ex4')
                    for target in remove_ind:
                        # os.remove(out_path + 'Indicators' + target + 'ex4')
                        # os.remove(center + 'Indicators' + target + 'ex4')
                        com.log('削除: ' + out_path + 'Indicators' + target + 'ex4')
                        com.log('削除: ' + center + 'Indicators' + target + 'ex4')
            else:
                if cst.IP == cst.WEB_IP:
                    for target in target_ea:
                        # shutil.copy2(center + 'Experts' + target + 'ex4', web_path + 'Experts')
                        com.log('コピー: ' + center + 'Experts' + target + 'ex4' + ' → ' + web_path + 'Experts')
                    for target in target_ind:
                        # shutil.copy2(center + 'Indicators' + target + 'ex4', web_path + 'Indicators')
                        com.log('コピー: ' + center + 'Indicators' + target + 'ex4' + ' → ' + web_path + 'Indicators')

                    for target in remove_ea:
                        # os.remove(center + 'Experts' + target + 'ex4')
                        com.log('削除: ' + center + 'Experts' + target + 'ex4')
                    for target in remove_ind:
                        # os.remove(center + 'Indicators' + target + 'ex4')
                        com.log('削除: ' + center + 'Indicators' + target + 'ex4')

                elif cst.IP == cst.MY_IP:
                    for target in target_ea:
                        # shutil.copy2(center + 'Experts' + target + 'ex4', my_path + 'Experts')
                        com.log('コピー: ' + center + 'Experts' + target + 'ex4' + ' → ' + my_path + 'Experts')
                    for target in target_ind:
                        # shutil.copy2(center + 'Indicators' + target + 'ex4', my_path + 'Indicators')
                        com.log('コピー: ' + center + 'Indicators' + target + 'ex4' + ' → ' + my_path + 'Indicators')

                    for target in remove_ea:
                        # os.remove(center + 'Experts' + target + 'ex4')
                        com.log('削除: ' + center + 'Experts' + target + 'ex4')
                    for target in remove_ind:
                        # os.remove(center + 'Indicators' + target + 'ex4')
                        com.log('削除: ' + center + 'Indicators' + target + 'ex4')
        else:
            com.log(fnc + ': 端末対象外 ' + cst.IPS[cst.IP])

        return True

    # TickstoryのCSVファイル編集
    def edit_history(self, fuc):

        return True

    # hstファイルのコピー
    def copy_history(self, fnc, in_path, out_path, hst_name):
        if cst.IP == cst.DEV_IP:

            is_interrupt = False
            total_time = 0
            try:
                for i in range(0, len(in_path)):

                    start_time = com.time_start()
                    hst_paths = os.listdir(cst.MT4_PATH + in_path[i] + '/history')

                    # ヒストリカルデータの対象サーバー名を検索
                    for hst_path in hst_paths:
                        if 0 <= hst_path.find(hst_name[i]):
                            break

                    files = os.listdir(cst.MT4_PATH + in_path[i] + '/history/' + hst_path)
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

                        shutil.copy2(cst.MT4_PATH + in_path[i] + '/history/' + hst_path + '/' + files[k],
                                     cst.MT4_PATH + 'MT4_TEST/' + out_path[i] + '/history/' + hst_path)
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
                    com.log('コピー完了(' + com.conv_time_str(run_time) + ')  [' + cst.MT4_PATH[:-1] + '] ' +
                            in_path[i] + ' → MT4_TEST/' + out_path[i])

            finally:
                try: window.close()
                except: pass

            com.log(fnc+ ': ' + ('中断' if is_interrupt else '全終了') + '(' + com.conv_time_str(total_time) + ')')
            com.dialog(('中断' if is_interrupt else '完了') + 'しました。(' + com.conv_time_str(total_time) + ')', fnc)

        else:
            com.log(fnc + ': 端末対象外 ' + cst.IPS[cst.IP])

        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False