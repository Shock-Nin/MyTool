#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd

from const import cst
from common import com
from business.multiple import web_login

import os.path
import argparse
import importlib
import threading
import pyautogui as pgui
import PySimpleGUI as sg
import subprocess
from subprocess import PIPE

CHANGE_MENU = 0

if 0 == CHANGE_MENU:
    menu1 = 'Win'
    menu2 = 'Mac'
else:
    menu1 = 'Mac'
    menu2 = 'Win'
BTNS = {
    menu1: {
        'Pochi': 'multiple.blog_pochi',
        'EAデータ編集': 'windows.ea_edits',
        'EAテスト結合': 'windows.ea_merge_test',
        'EAテスト': 'windows.ea_auto_test',
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

    wd = []

    # メニュー系CSV読み込み
    if not _get_menu():
        exit()

    # 通常の場合、画面表示
    if args.Function is None:
        com.log('ツール起動: ' + cst.PC)
        win_x, win_y = pgui.size()

        fold = [cst.MENU_CSV['Fold'].at[i, 'Name']
                for i in range(0, len((cst.MENU_CSV['Fold']))) if cst.MENU_CSV['Fold'].at[i, 'Type'] == cst.PC]
        web = [cst.MENU_CSV['Web'].at[i, 'Name'] for i in range(0, len((cst.MENU_CSV['Web'])))]

        layout = [[sg.Text('', key='act', background_color=cst.MAIN_ACT_COLOR[0], text_color=cst.MAIN_ACT_COLOR[1],
                           size=((11 if cst.PC == menu2 else 16), 1), font=('', 18),
                           pad=((0, 0), (0, 5)))],
                  [sg.Combo(fold, key='Fold', enable_events=True, readonly=True,
                            font=('', 16), size=((10 if cst.PC == menu2 else 15), 1), pad=((0, 0), (0, 5)))],
                  [sg.Combo(web, key='Web', enable_events=True, readonly=True,
                            font=('', 16), size=((10 if cst.PC == menu2 else 15), 1), pad=((0, 0), (0, 5)))],
                  [[sg.Button(btn, key=btn, font=('', 16), pad=((0, 0), (0, 5)),
                              size=((10 if cst.PC == menu2 else 15), 1))] for btn in BTNS[cst.PC]]]

        window = sg.Window(cst.PC, modal=True, element_justification='c', background_color=cst.MAIN_BGCOLOR,
                           element_padding=((0, 0), (0, 0)), margins=(0, 0), location=
                           ((win_x - WIN_X_MINUS, win_y - WIN_Y_MINUS)
                            if cst.PC == menu2 else (None, None)), layout=layout)
        # 画面のイベント監視
        while True:
            event, values = window.read()

            # 画面の×ボタンで終了
            if sg.WIN_CLOSED == event:
                com.log('ツール終了: ' + cst.PC)
                exit()

            # セレクト選択した場合
            if event in ['Fold', 'Web']:
                menu = cst.MENU_CSV[event]

                select = (menu[(menu['Type'] == cst.PC) & (menu['Name'] == values[event])]['Path'].values[0]
                          if 'Fold' == event else
                          menu[(menu['Name'] == values[event])])

                window['act'].update(event[0] + ': ' + values[event])
                window[event].update('')

                # Foldセレクトで選択した場合
                if 'Fold' == event:
                    subprocess.Popen(['explorer' if 'Win' == cst.PC else 'open',
                                      select.replace('/', '\\') if 'Win' == cst.PC else select])
                else:
                    wd.append(web_login.WebLogin('ログイン').do(select['Name'].values[0], select['URL'].values[0]))

            # ボタン選択した場合
            else:
                window['act'].update(event)

                # 動的モジュールを実行
                if 'Win' == cst.PC:
                    _run(event)
                # Macの場合は、並列で実行
                else:
                    thread1 = threading.Thread(name="thread1", target=_run, args=(event,))
                    thread1.start()
                    # thread1.join()

    # バッチの場合
    elif 'Batch' == args.Function:
        com.log(args.Function)

    # 機能単独起動の場合
    elif 0 < len(args.Function):
        com.log('Function開始:' + args.Function)
        _run(args.Function)
        com.log('Function終了:' + args.Function)


# 動的モジュールの実行
def _run(event):

    # subprocess.run(os.getcwd() + '/venv/bin python' + '.py', shell=True, stdout=PIPE, stderr=PIPE, text=True)
    # subprocess.run(os.getcwd() + '/venv/Scripts/python.exe' + '.py', shell=True, stdout=subprocess.PIPE, encoding="shift-jis")

    fnction = BTNS[cst.PC][event]
    module_name = 'business.' + fnction

    class_name = fnction.split('.')[len(fnction.split('.')) - 1]
    class_name = "".join([name[0].upper() + name[1:] for name in class_name.split('_')])

    instance = importlib.import_module(module_name)
    module = getattr(instance, class_name)
    return module(event).do()


# メニュー系CSV読み込み
def _get_menu():
    path = cst.GDRIVE_PATH[cst.PC] + 'menu/'
    err_msg = ''
    try:
        for file in cst.MENU_CSV:
            cst.MENU_CSV[file] = pd.read_csv(path + file + '.csv', encoding='cp932')

    except Exception as e:
        com.log('読み込みエラー: ' + path + file + ' |' + str(e))
        err_msg += '\n　' + path + file

    if 0 < len(err_msg):
        com.dialog('読み込みエラー\n' + err_msg, '読み込みエラー', 'E')
        return False

    return True


if __name__ == '__main__':

    # 引数受け取り
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--Function')
    args = parser.parse_args()
    main()
