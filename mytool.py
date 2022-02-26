#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windowsアプリ化コマンド
  pyinstaller mytool.spec --onefile

Macアプリ化コマンド
  python setup.py py2app
"""
from const import cst
from common import com
from batch import Batch
from business.multiple import web_login

import os
import argparse
import importlib
import pyautogui as pgui
import PySimpleGUI as sg
import subprocess

CHANGE_MENU = 0
MULTI_PROCESS = ['英単語']

if 0 == CHANGE_MENU:
    menu1 = 'Win'
    menu2 = 'Mac'
else:
    menu1 = 'Mac'
    menu2 = 'Win'
BTNS = {
    menu1: {
        'Pochi': 'multiple.blog_pochi',
        'EA連続テスト': 'windows.ea_auto_test',
        'EAテスト結合': 'windows.ea_merge_test',
        'EAデータ編集': 'windows.ea_edits',
    },
    menu2: {
        'Pochi': 'multiple.blog_pochi',
        '資産': 'mac.my_asset',
        '英単語': 'mac.eng1min',
    },
}
WIN_X_MINUS = 130
WIN_Y_MINUS = 160 + (int(len(BTNS['Mac']) + 2) * 22)


def main():

    processes = []
    # メニュー系CSV読み込み
    if not com.get_menu():
        return

    # 通常の場合、画面表示
    if args.Function is None:

        com.log('ツール起動: ' + cst.IP + ' | ' + cst.PC)
        win_x, win_y = pgui.size()
        event_time = 0

        # パスワード入力
        login = sg.Window('パスワード入力', keep_on_top=True, modal=True, element_justification='c',
                          background_color=cst.MAIN_BGCOLOR, margins=(20, 20),
                          icon=(os.getcwd() + cst.ICON_FILE), layout=
                          [[sg.Input('', key='pw', password_char='*', size=(16, 3), font=('', 30))],
                           [sg.Button('ログイン', key='login', font=('', 16), pad=((0, 0), (20, 0)),
                                      size=(16, 1))]])
        while True:
            event, values = login.read()

            # 画面の×ボタンで終了
            if sg.WIN_CLOSED == event:
                com.log('ツール終了: ' + cst.PC)
                return

            if 'login' == event:
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
                for i in range(0, len((cst.MENU_CSV['Fold']))) if cst.MENU_CSV['Fold'].at[i, 'Type'] == cst.PC]
        web = [cst.MENU_CSV['Web'].at[i, 'Name'] for i in range(0, len((cst.MENU_CSV['Web'])))]

        # メイン画面レイアウト
        layout = [[sg.Text('', key='act', background_color=cst.MAIN_ACT_COLOR[0], text_color=cst.MAIN_ACT_COLOR[1],
                           size=((11 if cst.PC == menu2 else 16), 1), font=('', 18),
                           pad=((0, 0), (0, 5)))],
                  [sg.Combo(fold, default_value='　Fold', key='Fold', enable_events=True, readonly=True,
                            font=('', 16), size=((10 if cst.PC == menu2 else 15), 1), pad=((0, 0), (0, 5)))],
                  [sg.Combo(web, default_value='　Web', key='Web', enable_events=True, readonly=True,
                            font=('', 16), size=((10 if cst.PC == menu2 else 15), 1), pad=((0, 0), (0, 15)))],
                  [[sg.Button(btn, key=btn, font=('', 16), pad=((0, 0), (0, 5)),
                              size=((10 if cst.PC == menu2 else 15), 1))] for btn in BTNS[cst.PC]]]

        window = sg.Window(cst.PC, modal=True, element_justification='c', background_color=cst.MAIN_BGCOLOR,
                           element_padding=((0, 0), (0, 0)), margins=(0, 0),
                           icon=(os.getcwd() + cst.ICON_FILE), location=
                           ((win_x - WIN_X_MINUS, win_y - WIN_Y_MINUS)
                            if cst.PC == menu2 else (None, None)), layout=layout)
        # 画面のイベント監視
        while True:
            event, values = window.read()

            # 画面の×ボタンで終了
            if sg.WIN_CLOSED == event:
                com.log('ツール終了: ' + cst.PC)
                return

            # セレクト選択した場合、ターミナルコマンドを実行
            if event in ['Fold', 'Web']:
                menu = cst.MENU_CSV[event]

                select = (menu[(menu['Type'] == cst.PC) & (menu['Name'] == values[event])]['Path'].values[0]
                          if 'Fold' == event else
                          menu[(menu['Name'] == values[event])])

                window['act'].update(event[0] + ': ' + values[event])
                window[event].update('　' + event[0].upper() + event[1:])

                # Foldセレクトで選択した場合
                if 'Fold' == event:
                    processes.append(
                        subprocess.Popen(['explorer' if 'Win' == cst.PC else 'open',
                                          select.replace('/', '\\') if 'Win' == cst.PC else select]))
                    com.log('フォルダ: ' + select)

                # Webセレクトで選択した場合
                else:
                    processes.append(
                        web_login.WebLogin('ログイン').do(select['Name'].values[0], select['URL'].values[0]))

            # ボタン選択した場合
            else:

                # 二度押し対策、10秒以内同一ボタン無効
                is_run = True
                if '  ' + event == window['act'].get():
                    is_run = int(com.conv_time_str(com.time_start() - event_time).replace(':', '')) < 10

                window['act'].update('  ' + event)

                # 動的モジュールを実行
                if is_run:
                    processes.append(subprocess.Popen(
                        [('C:/ProgramData/Anaconda3/envs/py39/python.exe' if 'Win' == cst.PC else
                          cst.CURRENT_PATH[cst.PC] + '/.conda/envs/py39/bin/python'),
                         os.getcwd() + '/run.py', '-m', BTNS[cst.PC][event], '-e', event]))

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

    function = BTNS[cst.PC][event]
    module_name = 'business.' + function

    class_name = function.split('.')[len(function.split('.')) - 1]
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
