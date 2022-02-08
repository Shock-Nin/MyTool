#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path

from const import cst
from common import com

import argparse
import importlib
import pyautogui as pgui
import PySimpleGUI as sg

BTN = {
    'Pochi': 'multiple.blog_pochi',
    '英語': 'mac.eng1min',
}
WIN_X_MINUS = 150
WIN_Y_MINUS = 120


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
        pochi = sg.Button('Pochi', key='Pochi', font=('', 16), size=(10, 1))
        eng1min = sg.Button('英語', key='英語', font=('', 16), size=(10, 1))
        layout = [[pochi], [eng1min]]

        window = sg.Window(cst.PC, modal=True, background_color=cst.MAIN_BGCOLOR,
                           location=(win_x - WIN_X_MINUS, win_y - WIN_Y_MINUS), layout=layout)
        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                com.log('ツール終了')
                exit()
            else:
                module_name = 'business.' + BTN[event]
                class_name = BTN[event].split('.')[len(BTN[event].split('.')) - 1]
                class_name = "".join([name[0].upper() + name[1:] for name in class_name.split('_')])

                instance = importlib.import_module(module_name)
                module = getattr(instance, class_name)
                is_end = module().do()


if __name__ == '__main__':
    main()
