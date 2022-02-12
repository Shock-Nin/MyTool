#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst
from common import com

import os.path
import argparse
import importlib
import threading
import pyautogui as pgui
import PySimpleGUI as sg
import subprocess
from subprocess import PIPE

CHANGE_MENU = 1

if 0 == CHANGE_MENU:
    menu1 = 'Win'
    menu2 = 'Mac'
else:
    menu1 = 'Mac'
    menu2 = 'Win'
BTNS = {
    menu1: {
        'Pochi': 'multiple.blog_pochi',
        'EAテスト': 'windows.ea_autotest',
        'EAパラメータ': 'windows.ea_edit_param',
        'EA成績(個別)': 'windows.ea_edit_unit',
    },
    menu2: {
        'Pochi': 'multiple.blog_pochi',
        '英単語': 'mac.eng1min',
    },
}
WIN_X_MINUS = 150
WIN_Y_MINUS = 170


def main():

    # ログフォルダの作成
    log_path = cst.TEMP_PATH[cst.PC] + 'Log'
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    # 通常の場合、画面表示
    if args.Function is None:
        com.log('ツール起動: ' + cst.PC)
        win_x, win_y = pgui.size()
        layout = [[sg.Button(btn, key=btn, font=('', 16), size=
                  ((10, 1) if cst.PC == menu2 else (15, 1)))] for btn in BTNS[cst.PC]]

        window = sg.Window(cst.PC, modal=True, background_color=cst.MAIN_BGCOLOR,
                           location=((win_x - WIN_X_MINUS, win_y - WIN_Y_MINUS)
                                     if cst.PC == menu2 else (None, None)), layout=layout)
        # 画面のイベント監視
        while True:
            event, values = window.read()

            # 画面の×ボタンで終了
            if event == sg.WIN_CLOSED:
                com.log('ツール終了: ' + cst.PC)
                exit()

            # 画面で選択した場合
            else:
                # 動的モジュールを、並列で実行
                # _run(event)
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


if __name__ == '__main__':

    # 引数受け取り
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--Function')
    args = parser.parse_args()
    main()
