#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path

from const import cst
from common import com

import argparse
import importlib
import pyautogui as pgui
import PySimpleGUI as sg

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

    # 引数受け取り
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--Batch')
    args = parser.parse_args()

    log_path = cst.TEMP_PATH[cst.PC] + 'Log'
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    # バッチの場合
    if 'Batch' == args.Batch:
        com.log('Batch')

    # 通常の場合、画面表示
    else:
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
                module_name = 'business.' + BTNS[cst.PC][event]
                class_name = BTNS[cst.PC][event].split('.')[len(BTNS[cst.PC][event].split('.')) - 1]
                class_name = "".join([name[0].upper() + name[1:] for name in class_name.split('_')])

                instance = importlib.import_module(module_name)
                module = getattr(instance, class_name)
                is_end = module().do()

                if is_end is None:
                    pass
                elif 0 < len(is_end):
                    com.dialog(is_end[0], is_end[1], is_end[2])
                else:
                    com.dialog('[' + event + ']が完了しました。', '正常終了')


if __name__ == '__main__':
    main()
