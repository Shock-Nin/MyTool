#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst

import PySimpleGUI as sg


# 標準ダイアログをレベルに応じて表示
def dialog(msg, title, lv=''):

    color = '#FF7777' if 'E' == lv else 'FFFF77' if 'W' == lv else '#77CCFF'
    window = sg.Window(title, keep_on_top=True, modal=True, background_color=color, element_justification='c', layout=[
        [sg.Column([[sg.Text(msg, background_color=color, text_color='#000000', font=('', 16), pad=((0, 0), (0, 0)))]],
                   size=(500, 300), scrollable=True, vertical_scroll_only=True, background_color=color)],
        [sg.Button('OK', key='OK', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')]])

    while True:
        event, values = window.read(timeout=0)
        if event in [sg.WIN_CLOSED, 'OK']:
            break
    window.close()


# 確認ダイヤログ
def question(msg, title, lv='', cancel=False):

    color = '#FF7777' if 'E' == lv else 'FFFF77' if 'W' == lv else '#77CCFF'
    btn = [sg.Button('はい', key='はい', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#777777'),
           sg.Button('いいえ', key='いいえ', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#777777')]
    if cancel:
        btn.append(sg.Button('中断', key='中断', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#555555'))
    window = sg.Window(title, keep_on_top=True, modal=True, background_color=color, element_justification='c', layout=[
        [sg.Text(msg, background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (20, 10)))], btn])

    flg = 0
    while True:
        event, values = (window.read() if 'Win' == cst.PC else window.read(timeout=0))
        if event in [sg.WIN_CLOSED, '中断']:
            break
        elif 'はい' == event:
            flg = 1
            break
        elif 'いいえ' == event:
            flg = -1
            break

    window.close()
    return flg


# 進捗表示
def progress(title, bar1, bar2=None, bar3=None):

    color = '#FFCCCC'
    lists = [bar1]
    if bar2 is not None:
        lists.append(bar2)
    if bar3 is not None:
        lists.append(bar3)

    window = sg.Window(
        title, keep_on_top=True, no_titlebar=True, modal=True, element_justification='c', background_color=color,layout=[
            [sg.Text(title, background_color=color, text_color='#000000', font=('', 16), pad=((10, 10), (20, 10)))],[[
                [sg.Text(bar[0], key=bar[0], background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (5, 5)))],
                [sg.ProgressBar(key=bar[0] + '_', max_value=bar[1], bar_color='#008000', size=(30, 20), pad=((15, 15), (5, 5)))]]
                for bar in lists], [sg.Text('', background_color=color)]])

    return window


# 完了ダイアログ
def close(is_event):

    # 中断の場合、何もしない
    if is_event is None:
        pass
    # エラーの場合、エラーダイアログ
    elif type(is_event) == list:
        dialog(is_event[0], is_event[1], is_event[2])

    # 正常終了の場合、完了ダイアログ
    else:
        dialog('[' + is_event + ']が完了しました。', '正常終了')
