#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import os
import cv2
import glob
import shutil
import datetime
import subprocess
import pandas as pd
import PySimpleGUI as sg


class Function:

    def __init__(self, job, ip):
        self.myjob = job
        self.ip = ip

    def do(self, fnc):

        if fnc in ['Tickヒストリー編集']:
            if com.question(fnc + ' 開始しますか？', '開始確認') <= 0:
                return

        if fnc in ['最適化セット', '最適化起動', 'MT4起動']:
            self.set_optimize(
                fnc, opt_path=['MT4_DEV/OANDA', 'MT4_TEST/Test1', 'MT4_TEST/Test1_2', 'MT4_TEST/Test1_3'],
                affinity=['F', '2', '4', '8'],
                dev_path={'MT4起動': 'MT4_DEV/OANDA'},
                web_path=['ForexExchange', 'Rakuten'],
                my_path=['OANDA', 'FXTF'],  # 'FxPro', 'MyFx', 'XM'
            )
        elif 'EX4コピー' == fnc:
            # コピー(target)はワイルドカード、削除(remove)は完全一致
            self.copy_ex4(
                fnc, dev_out=['Test1', 'Test1_2', 'Test1_3', 'Test2', 'Test2_2'],
                web_path=['ForexExchange', 'Rakuten'],
                my_path=['OANDA', 'Rakuten1', 'Rakuten2'],
                target_ea=['Shocknin', 'WheSitDoch'],
                target_ind=['Shocknin', 'WheSitDoch'],
                remove_ea=['ShockninWhesitdoch', 'ShockninMaster', 'AnomalyShocknin', 'AnomalyGoToBe'],
                remove_ind=['AnomalyShocknin_AUDUSD', 'AnomalyShocknin_EURUSD', 'AnomalyShocknin_GBPUSD', 'AnomalyShocknin_GOLD',
                            'AnomalyShocknin_NZDUSD','AnomalyShocknin_USDCAD','AnomalyShocknin_USDCHF','AnomalyShocknin_USDJPY',
                            'ShockninMaster_AUDUSD','ShockninMaster_EURUSD','ShockninMaster_GBPUSD','ShockninMaster_GOLD','ShockninMaster_USDJPY',
                            'sts_ind_JikanDeGo','sts_ind_WheSitaDoch','WheSitaDoch','WheSitaDoch_X','WheSitDoch - コピー','WheSitDoch_Box',
                            'WheSitDoch_']
            )
        elif 'MT4ログ削除' == fnc:
            self.log_delete(fnc)

        elif 'Tickヒストリー編集' == fnc:
            self.edit_history(fnc)

        elif 'hstコピー(テスト)' == fnc:
            self.copy_history_test(
                fnc, in_path=['MT4_DEV/OANDA', 'MT4_DEV/OANDA'],
                out_path=['Test1', 'Test2'],
                hst_name=['Demo', 'Demo']
            )
        # elif 'hst転送(Web)' == fnc:
        #     self.copy_history_web(fnc, in_path='MT4_DEV/OANDA', hst_name='Demo')
        else:
            target = ''
            if 'MQL編集' == fnc:
                target = cst.MT4_DEV['Win'] + 'metaeditor.exe /portable'
            elif 'Winアップデート' == fnc:
                target = os.getcwd() + '/item/app/Wub/Wub.exe'
            elif 'Tickstory' == fnc:
                target = cst.TICK_STORY

            if 0 < len(target):
                return subprocess.Popen(target)

        return []

    # 最適化MT4起動と、set読み込み
    def set_optimize(self, fnc, opt_path, affinity, dev_path, web_path, my_path):
        if 'Win' == cst.PC:

            # MT4起動コマンドを設定
            commands = []
            if cst.IP == cst.DEV_IP:
                if 0 <= fnc.find('最適化'):
                    for i in range(0, len(opt_path)):
                        commands.append(
                            'cmd /c start "" /affinity ' + (affinity[i] + ' "' + cst.MT4_PATH + opt_path[i] +
                                                            '/terminal.exe"').replace('/', '\\') + ' "/portable"')
                else:
                    commands.append(cst.MT4_PATH + dev_path[fnc] + '/terminal.exe /portable')

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
            if expert_x is None:
                for i in range(0, len(commands)):
                    com.log('起動: ' + commands[i])
                    subprocess.Popen(commands[i])
                    com.sleep(1)
                com.sleep(5)
            else:
                com.dialog('MT4起動済みです。', title=fnc)

            if '最適化セット' == fnc:
                com.sleep(3)

                # 全体画面の撮影
                shot, gray = com.shot_grab()
                if shot is None:
                    return False

                for i in range(1, len(commands)):
                    subprocess.Popen(commands[i])
                    com.sleep(5)

                    com.click_pos(expert_x + 5, expert_y + 5)
                    com.sleep(3)

                    # 全体画面の撮影
                    shot, gray = com.shot_grab()
                    com.sleep(2)

                    # 読み込みボタン
                    read_x, read_y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' +
                                               cst.MATCH_IMG_MT4['読み込み'], (0, 255, 255))
                    # 最適化チェック
                    opt_x, opt_y = com.match(shot, gray, cst.MATCH_PATH + 'auto_test/' +
                                             cst.MATCH_IMG_MT4['最適化OFF'], (255, 0, 255))
                    try:
                        com.click_pos(read_x + 5, read_y + 5)
                    except:
                        com.dialog('メニュー位置をスタート横に変更してください。', title='メニュー位置エラー', lv='w')
                        return False
                    com.sleep(3)

                    com.clip_copy((cst.GDRIVE_PATH['Win'] + 'FX/Presets/開発用.set').replace('/', '\\'), True)
                    com.sleep(3)
                    com.click_pos(read_x + 5, read_y + 40)
                    com.sleep(3)

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

            msg = []
            center = cst.GDRIVE_PATH['Win'] + 'FX/MQL4/'

            # 開発端末の場合、テスト用と転送用(GoogleDrive)にコピー
            if cst.IP == cst.DEV_IP:
                in_path = cst.MT4_PATH + 'MT4_DEV/OANDA/MQL4/'
                msg.append(in_path + ' → ')

                for out in dev_out:
                    out_path = cst.MT4_PATH + 'MT4_TEST/' + out + '/MQL4/'

                    for target in target_ea:
                        self._copy_ex4_sub(in_path, out_path, 'Experts', target)
                        self._copy_ex4_sub(in_path, center, 'Experts', target)
                    for target in target_ind:
                        self._copy_ex4_sub(in_path, out_path, 'Indicators', target)
                        self._copy_ex4_sub(in_path, center, 'Indicators', target)

                    for target in remove_ea:
                        self._delete_ex4_sub(out_path, 'Experts', target)
                    for target in remove_ind:
                        self._delete_ex4_sub(out_path, 'Indicators', target)

                    msg.append('　' + out_path)
                msg.append('　' + center)

            # 開発端末以外の場合、転送用(GoogleDrive)から運用MT4にコピー
            else:
                path = (web_path if cst.IP == cst.WEB_IP else my_path)
                msg.append(center + ' → ')

                for out in path:
                    out_path = cst.MT4_PATH + out + '/MQL4/'

                    for target in target_ea:
                        self._copy_ex4_sub(center, out_path, 'Experts', target)
                    for target in target_ind:
                        self._copy_ex4_sub(center, out_path, 'Indicators', target)

                    for target in remove_ea:
                        self._delete_ex4_sub(out_path, 'Experts', target)
                    for target in remove_ind:
                        self._delete_ex4_sub(out_path, 'Indicators', target)

                    msg.append('　' + out_path)

            com.log(fnc + '完了')
            com.dialog(fnc + '完了しました(' + str(len(msg) - 1) + ')\n\n' +
                       "".join(['\n　' + row.replace(cst.MT4_PATH, '') for row in msg]), fnc + ' 完了')
        else:
            com.log(fnc + ': 端末対象外 ' + cst.IPS[cst.IP])

        return True

    # コピーの実行
    def _copy_ex4_sub(self, in_path, out_path, file_type, target):

        files = os.listdir(in_path + file_type)
        files = [file for file in files if 0 <= file.find(target) and 0 <= file.find('.ex4')]

        for file in files:
            shutil.copy2(in_path + file_type + '/' + file, out_path + file_type)
            com.log('ex4コピー: ' + in_path.replace(cst.MT4_PATH, '') + file_type + '/' + file + ' → ' +
                    out_path.replace(cst.MT4_PATH, '') + file_type)

    # 削除の実行
    def _delete_ex4_sub(self, delete_path, file_type, target):

        if os.path.exists(delete_path + file_type + '/' + target + '.ex4'):
            os.remove(delete_path + file_type + '/' + target + '.ex4')
            com.log('ex4削除: ' + delete_path.replace(cst.MT4_PATH, '') + file_type + '/' + target + '.ex4')

    # ログとテストヒストリカルデータの削除
    def log_delete(self, fnc):
        if 'Win' == cst.PC:

            deletes = [['logs', '.log'], ['tester/logs', '.log'], ['tester/history', '.fxt'], ['tester/caches', '.0']]
            paths = []

            paths1 = os.listdir(cst.MT4_PATH)
            for path1 in paths1:

                if path1.endswith('.txt') or os.path.exists(cst.MT4_PATH + path1 + '/terminal.exe'):
                    paths.append(cst.MT4_PATH + path1)
                    continue

                paths2 = os.listdir(cst.MT4_PATH + path1)
                for path2 in paths2:
                    if os.path.exists(cst.MT4_PATH + path1 + '/' + path2 + '/terminal.exe'):
                        paths.append(cst.MT4_PATH + path1 + '/' + path2)
                        continue

            msg = []
            for path in paths:
                for i in range(0, len(deletes)):

                    files = os.listdir(path + '/' + deletes[i][0])
                    files = [file for file in files if 0 <= file.find(deletes[i][1])]

                    for file in files:
                        target = path + '/' + deletes[i][0] + '/' + file
                        try:
                            os.remove(target)
                            msg.append(target)
                            com.log('MT4ログ削除: ' + target)
                        except:
                            msg.append('エラー: ' + target)
                            com.log('MT4ログ削除エラー: ' + target)

            com.log(fnc + '完了(' + str(len(msg)) + ')')
            com.dialog(fnc + '完了しました(' + str(len(msg)) + ')\n' +
                       ('削除はありませんでした。' if 0 == len(msg) else
                       '\n　' + cst.MT4_PATH[:-1] + "".join(['\n　　' + row.replace(cst.MT4_PATH, '')
                                                            for row in msg])), fnc + ' 完了')

    # TickstoryのCSVファイルマージ・編集
    def edit_history(self, fnc):
        if self.ip == cst.DEV_IP:

            is_interrupt = False
            total_time = 0

            out_path = cst.HST_PATH[cst.PC]
            base_files = glob.glob(out_path + '/2024/*.csv')
            add_files = glob.glob(out_path + '/add/*.csv')

            if 0 == len(add_files):
                com.dialog(out_path + '/addにファイルが存在しません。', title='ファイル不在', lv='w')
                return

            err_msg = ''
            try:
                for i in range(len(base_files)):

                    start_time = com.time_start()

                    # 進捗表示
                    file = base_files[i].split('\\')[-1]

                    window = com.progress('ヒストリカルデータ編集中', [file, len(base_files)], interrupt=True)
                    event, values = window.read(timeout=0)

                    window[file].update(file + ' (' + str(i) + ' / ' + str(len(base_files)) + ')')
                    window[file + '_'].update(i)

                    add_data = pd.read_csv(out_path + '/add/' + file)
                    before_len = len(add_data)

                    add_data = add_data[(add_data['Date'].astype(str).str.match('20..0101') == False)
                                        & (pd.to_datetime(add_data['Date'], format='%Y%m%d').dt.weekday < 5)]
                    add_data = add_data.reset_index(drop=True)

                    com.log(file + ' (' + str(len(add_data) - before_len) + ') | '
                            + str(before_len) + ' ⇒ ' + str(len(add_data)))
                    num = ((add_data['High'] - add_data['Low']) / add_data['Close'] * 10000).astype(int)

                    for k in range(len(add_data)):
                        add_data.at[add_data.index[k], 'Volume'] = (4 if num[k] < 4 else num[k]) * 10 / 10

                        if 0 == k % 1000000 and 0 < k:
                            print(file + ': ' + str(k) + ' / ' + str(len(add_data)))

                        # 中断イベント
                        if _is_interrupt(window, event):
                            is_interrupt = True
                            break

                    # 中断送り
                    if is_interrupt:
                        break

                    run_time = com.time_end(start_time)
                    com.log('Volume編集完了(' + com.conv_time_str(run_time) + ') ' + file)

                    try:
                        result = pd.concat([pd.read_csv(out_path + '/' + file, encoding='cp932'), add_data])
                        result.to_csv(out_path + '/' + file, index=False)

                    except Exception as e:
                        err_msg += '\n　' + file + '\n　　' + str(e)
                        com.log(str(e))
                        continue

                    # 中断イベント
                    if _is_interrupt(window, event):
                        is_interrupt = True
                        break

                    run_time = com.time_end(start_time)
                    total_time += run_time
                    com.log('マージ完了(' + com.conv_time_str(run_time) + ') ' + file)

                    window.close()
            finally:
                try: window.close()
                except: pass

            com.log(fnc + ': ' + ('中断' if is_interrupt else '全終了') + '(' + com.conv_time_str(total_time) + ')' +
                    (' エラーあり' if 0 < len(err_msg) else ''), lv=('W' if 0 < len(err_msg) else None))
            com.dialog(('中断' if is_interrupt else '完了') + 'しました。(' + com.conv_time_str(total_time) + ')' +
                       ('\n以下でエラーが発生しました。\n' + err_msg if 0 < len(err_msg) else ''),
                       fnc, lv=('W' if 0 < len(err_msg) else None))

        else:
            com.log(fnc + ': 端末対象外 ' + cst.IPS[cst.IP])

        return True

    # hstファイルのコピー(テスト用)
    def copy_history_test(self, fnc, in_path, out_path, hst_name):
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

            com.log(fnc + ': ' + ('中断' if is_interrupt else '全終了') + '(' + com.conv_time_str(total_time) + ')')
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