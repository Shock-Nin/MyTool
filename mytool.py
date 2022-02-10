#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path

from const import cst
from common import com

import argparse
import importlib
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
        'EAテスト': 'windows.ea_autotest',
        'EAパラメータ': 'windows.ea_edit_param',
        'EAデータ集計': 'windows.ea_edit_data',
    },
    menu2: {
        'Pochi': 'multiple.blog_pochi',
        '英語': 'mac.eng1min',
    },
}
WIN_X_MINUS = 150
WIN_Y_MINUS = 170


def main():

    log_path = cst.TEMP_PATH[cst.PC] + 'Log'
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    # 通常の場合、画面表示
    if args.Function is None:
        com.log('Open')
        win_x, win_y = pgui.size()
        layout = [[sg.Button(btn, key=btn, font=('', 16), size=(15, 1))] for btn in BTNS[cst.PC]]

        window = sg.Window(cst.PC, modal=True, background_color=cst.MAIN_BGCOLOR,
                           location=((win_x - WIN_X_MINUS, win_y - WIN_Y_MINUS)
                                     if cst.PC == menu2 else (None, None)), layout=layout)
        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                com.log('ツール終了')
                exit()
            else:
                is_end = None
                if event in cst.SINGLE:
                    command = ' mytool.py -f ' + BTNS[cst.PC][event]
                    if 'Mac' == cst.PC:
                        subprocess.run('python' + command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
                    else:
                        subprocess.run(os.getcwd() + '/venv/Scripts/python.exe' + command, shell=True, stdout=subprocess.PIPE, encoding="shift-jis")
                else:
                    is_end = _run(BTNS[cst.PC][event])

                if is_end is None:
                    pass
                elif 0 < len(is_end):
                    com.dialog(is_end[0], is_end[1], is_end[2])
                else:
                    com.dialog('[' + event + ']が完了しました。', '正常終了')

    # バッチの場合
    elif 'Batch' == args.Function:
        com.log('Batch')

    # 機能単独起動の場合
    elif 0 < len(args.Function):
        com.log('Function開始:' + args.Function)
        _run(args.Function)
        com.log('Function終了:' + args.Function)


def _run(fnction):
    module_name = 'business.' + fnction
    class_name = fnction.split('.')[len(fnction.split('.')) - 1]
    class_name = "".join([name[0].upper() + name[1:] for name in class_name.split('_')])

    instance = importlib.import_module(module_name)
    module = getattr(instance, class_name)
    return module().do()


if __name__ == '__main__':
    # 引数受け取り
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--Function')
    args = parser.parse_args()
    main()
