#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst
from common import com
from business.multiple import web_login
from batch import Batch

import os
import requests
import argparse
import importlib
import threading
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
        'EAテスト': 'windows.ea_auto_test',
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

    my_ip = requests.get('https://ifconfig.me').text

    # 通常の場合、画面表示
    if args.Function is None:
        com.log('ツール起動: ' + my_ip + ' | ' + cst.PC)
        win_x, win_y = pgui.size()

        fold = [cst.MENU_CSV['Fold'].at[i, 'Name']
                for i in range(0, len((cst.MENU_CSV['Fold']))) if cst.MENU_CSV['Fold'].at[i, 'Type'] == cst.PC]
        web = [cst.MENU_CSV['Web'].at[i, 'Name'] for i in range(0, len((cst.MENU_CSV['Web'])))]

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
            com.sleep(1)

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
                window['act'].update('  ' + event)

                # 動的モジュールを実行
                processes.append(subprocess.Popen(
                    ['python', os.getcwd() + '/run.py', '-m', BTNS[cst.PC][event], '-e', event]))

                # # 動的モジュールを実行
                # if 'Win' == cst.PC:
                #     processes.append(_run(event))
                #
                # # Macの場合は、並列で実行
                # else:
                #     processes.append(subprocess.Popen(
                #         ['python', os.getcwd() + '/run.py', '-m', BTNS[cst.PC][event], '-e', event]))
                #
                #     # if event in MULTI_PROCESS:
                #     #     thread1 = threading.Thread(name="thread1", target=_run, args=(event,))
                #     #     processes.append(thread1.start())
                #     #     # thread1.join()
                #     # else:
                #     #     processes.append(_run(event))

    # バッチ起動の場合
    elif 'Batch' == args.Function:
        msg = Batch(args.Function).do()
        if 0 < len(msg):
            com.log('Batch終了: ' + msg)
        else:
            com.log('Batch稼働なし: ' + my_ip)

    # 機能単独起動の場合
    elif 0 < len(args.Function):
        com.log('Function開始: ' + args.Function)
        _run(args.Function)
        com.log('Function終了: ' + args.Function)


# 動的モジュールの実行
def _run(event):

    fnction = BTNS[cst.PC][event]
    module_name = 'business.' + fnction

    class_name = fnction.split('.')[len(fnction.split('.')) - 1]
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
