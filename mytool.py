#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windowsアプリ化コマンド
  pyinstaller mytool_exe.spec --clean --icon=item/img/logo.ico

Macアプリ化コマンド
  python mytool_app.py py2app
"""
from const import cst
from common import com
from batch import Batch
from business.multiple import web_login
from business.windows import function

import os
import argparse
import importlib
import pyautogui as pgui
import PySimpleGUI as sg
import subprocess

""" PW_INPUT = True | CHANGE_MENU = -1 """
PW_INPUT = False
CHANGE_MENU = -1
""" ---------------------------------- """
BTNS = {cst.DEV_IP: {
    'Pochi': 'multiple.blog_pochi',
    }, cst.WEB_IP: {
    'Pochi': 'multiple.blog_pochi',
    }, cst.MY_IP: {
    'Pochi': 'multiple.blog_pochi',
    }, cst.MAC_IP: {
    'Pochi': 'multiple.blog_pochi',
    '資産': 'mac.my_asset',
    '英単語': 'mac.eng1min',
    }}
EA_MENU = {
    'EA連続テスト': 'windows.ea_auto_test',
    'EAテスト結合': 'windows.ea_merge_test',
    'EAデータ編集': 'windows.ea_edits',
}
FUNC_MENU = {
    '最適化セット': 'DEV',
    'MT4起動': 'ALL',
    'MQL編集': 'DEV',
    'EX4コピー': 'ALL',
    'MT4ログ削除': 'ALL',
    '週間レート': 'DEV',
    'Winアップデート': 'ALL',
    'ヒストリカル編集': 'DEV',
    'ヒストリカルコピー': 'DEV',
    'Tickstory': 'DEV',
}
WORK_IP = (cst.IP if CHANGE_MENU < 0 else cst.IP_LIST[CHANGE_MENU])
BTN = BTNS[WORK_IP]
HEIGHT = 2 + (1 if cst.DEV_IP == WORK_IP else 0) + (1 if cst.MAC_IP != WORK_IP else 0)
DP_XY_WIDTH = {
    cst.DEV_IP: [0, 100 + (int(len(BTN) + HEIGHT) * 70), 16, 2],
    cst.WEB_IP: [0, 0, 20, 2],
    cst.MY_IP: [0, 0, 20, 2],
    cst.MAC_IP: [150, 80 + (int(len(BTN) + HEIGHT) * 40), 13, 1]}
DP = DP_XY_WIDTH[WORK_IP]
XY_SIZE = (DP[2], 1)


def main():

    processes = []
    # メニュー系CSV読み込み
    if not com.get_menu():
        return

    # 通常の場合、画面表示
    if args.Function is None:

        com.log(cst.PC + ' : ' + cst.PC_NAME + ' : ' + cst.IP)
        win_x, win_y = pgui.size()
        event_time = 0

        # パスワード入力
        if PW_INPUT:
            login = sg.Window('パスワード入力', keep_on_top=True, modal=True, element_justification='c',
                              background_color=cst.MAIN_BGCOLOR, margins=(20, 20),
                              icon=(os.getcwd() + cst.ICON_FILE), return_keyboard_events=True, layout=
                              [[sg.Input('', key='pw', password_char='*', font=('', 30), size=(12, 3))],
                               [sg.Button('ログイン', key='login', font=('', 16), size=(12, 1), pad=((0, 0), (20, 0)))]])
            while True:
                event, values = login.read()

                # 画面の×ボタンで終了
                if sg.WIN_CLOSED == event:
                    com.log('ツール終了: ' + cst.PC)
                    return

                if event in ['login', '\r', 'Return:603979789']:
                    account = cst.MENU_CSV['PwBank'][('楽天カード' == cst.MENU_CSV['PwBank']['SITE'])]
                    # 正常ログイン
                    if account['PASS'].values[0] == values['pw']:
                        com.log('ツール正常ログイン')
                        login.close()
                        break

                    # パスワード不整合の場合は、アラートメール送信
                    elif 0 < len(values['pw']):
                        login['pw'].update('')
                        com.log('ツール不正ログイン: ' + values['pw'])
                        com.dialog('パスワードが不一致です。', 'ログイン不正', 'E')
                        com.send_mail('不正ログイン', cst.IPS[cst.IP] + '[' + cst.IP + ']<br>' +
                                      'にて不正ログイン発生(' + values['pw'] + ')', account['ID1'].values[0],
                                      account=cst.ERROR_MAIL, password=cst.ERROR_MAIL_PW)

        # コンボボックスのメニュー作成
        fold = [cst.MENU_CSV['Fold'].at[i, 'Name']
                for i in range(0, len(cst.MENU_CSV['Fold']))
                if cst.MENU_CSV['Fold'].at[i, 'Type'] in [cst.PC, cst.IPS[WORK_IP]]]
        web = [cst.MENU_CSV['Web'].at[i, 'Name'] for i in range(0, len(cst.MENU_CSV['Web']))]

        # メイン画面レイアウト
        layout = [[sg.Text('', key='act', background_color=cst.MAIN_ACT_COLOR[0], text_color=cst.MAIN_ACT_COLOR[1],
                           font=('', 18 * DP[3]), size=XY_SIZE, pad=((0, 0), (0, 5)))],
                  [sg.Combo(fold, default_value='　Fold', key='Fold', enable_events=True, readonly=True,
                            font=('', 16 * DP[3]), size=XY_SIZE, pad=((0, 0), (0, 5)))],
                  [sg.Combo(web, default_value='　Web', key='Web', enable_events=True, readonly=True,
                            font=('', 16 * DP[3]), size=XY_SIZE, pad=((0, 0), (0, 15)))],
                  [[sg.Button(btn, key=btn, font=('', 16 * DP[3]), pad=((0, 0), (0, 5)), size=XY_SIZE)] for btn in BTN]]

        is_dev = (cst.DEV_IP == WORK_IP)
        if is_dev:
            layout.append([sg.Combo([key for key in EA_MENU],
                                    default_value='　EA', key='EA', enable_events=True, readonly=True,
                                    font=('', 16 * DP[3]), size=XY_SIZE, pad=((0, 0), (10, 5)))])
        if cst.MAC_IP != WORK_IP:
            layout.append([sg.Combo([key for key in FUNC_MENU if is_dev or (not is_dev and 'ALL' == FUNC_MENU[key])],
                                    default_value='　機能', key='機能', enable_events=True, readonly=True,
                                    font=('', 16 * DP[3]), size=XY_SIZE, pad=((0, 0), (0, 5)))])

        location = (None, None) if 0 == DP[0] + DP[1] else (
            win_x - DP[0] if 0 < DP[0] else 0, win_y - DP[1] if 0 < DP[1] else 0)

        window = sg.Window(cst.PC, modal=True, keep_on_top=True, element_justification='c',
                           icon=(os.getcwd() + cst.ICON_FILE),
                           background_color=(cst.MAIN_BGCOLOR if CHANGE_MENU < 0 else '#777777'),
                           element_padding=((0, 0), (0, 0)), margins=(0, 0), location=location, layout=layout)
        # 画面のイベント監視
        while True:
            event, values = window.read()

            # 画面の×ボタンで終了
            if sg.WIN_CLOSED == event:
                com.log('ツール終了')
                return

            # セレクト選択した場合、ターミナルコマンドを実行
            if event in ['Fold', 'Web', 'EA', '機能']:

                if event in ['Fold', 'Web']:
                    menu = cst.MENU_CSV[event]

                try:
                    select = (menu[(menu['Type'] == cst.PC) & (menu['Name'] == values[event])]['Path'].values[0]
                              if 'Fold' == event else
                              menu[(menu['Name'] == values[event])]
                              if 'Web' == event else
                              values[event]
                              if 'EA' == event else
                              values[event])
                except: continue

                window['act'].update(event[0] + ': ' + values[event])
                window[event].update('　' + event[0].upper() + event[1:])

                # Foldセレクトで選択した場合
                if 'Fold' == event:
                    processes.append(
                        subprocess.Popen(['explorer' if 'Win' == cst.PC else 'open',
                                          select.replace('/', '\\') if 'Win' == cst.PC else select]))
                    com.log('フォルダ: ' + select)

                # Webセレクトで選択した場合
                elif 'Web' == event:
                    processes.append(
                        web_login.WebLogin('ログイン').do(select['Name'].values[0], select['URL'].values[0]))

                # EAセレクトで選択した場合
                elif 'EA' == event:
                    # 動的モジュールを実行
                    processes.append(subprocess.Popen(
                        [cst.RUN_PATH[cst.PC], os.getcwd() + '/run.py', '-m', EA_MENU[select], '-e', select]))

                # 単独機能で選択した場合
                else:
                    processes.append(function.Function(event, WORK_IP).do(select))

            # ボタン選択した場合
            else:

                # 二度押し対策、5秒以内同一ボタン無効
                is_run = True
                if '  ' + event == window['act'].get():
                    is_run = 5 < int(com.conv_time_str(com.time_start() - event_time).replace(':', ''))

                window['act'].update('  ' + event)

                # 動的モジュールを実行
                if is_run:
                    processes.append(subprocess.Popen(
                        [cst.RUN_PATH[cst.PC], os.getcwd() + '/run.py', '-m', BTN[event], '-e', event]))

            event_time = com.time_start()

    # バッチ起動の場合
    elif 'Batch' == args.Function:
        msg = Batch(args.Function).do()
        if 0 < len(msg):
            com.log('Batch終了: ' + msg)
        else:
            com.log('Batch稼働なし: ' + cst.IP)

    # 機能単独起動の場合
    elif 0 < len(args.Function):
        com.log('Function開始: ' + args.Function)
        _run(args.Function)
        com.log('Function終了: ' + args.Function)


# 動的モジュールの実行
def _run(event):
    fnc = BTN[event]
    module_name = 'business.' + fnc

    class_name = fnc.split('.')[len(fnc.split('.')) - 1]
    class_name = "".join([name[0].upper() + name[1:] for name in class_name.split('_')])

    instance = importlib.import_module(module_name)
    module = getattr(instance, class_name)
    return module(event).do()


if __name__ == '__main__':
    # 引数受け取り
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--Function')
    args = parser.parse_args()
    main()
