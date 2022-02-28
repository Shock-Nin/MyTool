#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst

import os
import PySimpleGUI as sg


# 標準ダイアログをレベルに応じて表示
def dialog(msg, title, lv=''):

    color = '#FF7777' if 'E' == lv else '#FFFF77' if 'W' == lv else '#77CCFF'
    txt = [sg.Text(msg, background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (10, 10)))]
    if len(msg) < 100:
        layout = txt
    else:
        layout = [sg.Column([txt], size=(500, 300), scrollable=True, background_color=color)]

    window = sg.Window(title, keep_on_top=True, modal=True, background_color=color,
                       icon=(os.getcwd() + cst.ICON_FILE), return_keyboard_events=True, element_justification='c',
                       layout=[layout, [sg.Button('OK', key='OK', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')]])

    while True:
        if 'Mac' == cst.PC:
            event, values = window.read(timeout=0)
        else:
            event, values = window.read()
        if event in [sg.WIN_CLOSED, 'OK', '\r', 'Return:603979789']:
            break
    window.close()


# 確認ダイヤログ
def question(msg, title, lv='', cancel=False):

    color = '#FF7777' if 'E' == lv else '#FFFF77' if 'W' == lv else '#77CCFF'
    btn = [sg.Button('はい', key='はい', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#777777'),
           sg.Button('いいえ', key='いいえ', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#777777')]
    if cancel:
        btn.append(sg.Button('中断', key='中断', font=('', 16), pad=((10, 10), (10, 20)), size=(6, 1), button_color='#555555'))
    window = sg.Window(title, keep_on_top=True, modal=True, background_color=color,
                       icon=(os.getcwd() + cst.ICON_FILE), return_keyboard_events=True, element_justification='c',
                       layout=[[sg.Text(msg, background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (20, 10)))], btn])

    flg = 0
    while True:
        if 'Mac' == cst.PC:
            event, values = window.read(timeout=0)
        else:
            event, values = window.read()
        if event in [sg.WIN_CLOSED, '中断']:
            break
        elif event in ['はい', '\r', 'Return:603979789']:
            flg = 1
            break
        elif 'いいえ' == event:
            flg = -1
            break

    window.close()
    return flg


# 表形式向けダイヤログ
def dialog_cols(msg, cols, aligns, title, obj='', lv=''):

    color = '#FF7777' if 'E' == lv else '#FFFF77' if 'W' == lv else '#77CCFF'

    if 'check' == obj:
        center = [
            sg.Column([[
                sg.Checkbox(row, True, key=row, background_color=color, text_color='#000000', pad=((0, 0), (0, 0)), font=('', 16))]
                for row in cols[i]], element_justification=aligns[i], background_color=color, vertical_alignment='bottom')
            for i in range(0, len(cols))]
        btn = [sg.Button('全て外す', key='check_out', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777'),
               sg.Button('開始', key='Start', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777'),
               sg.Button('キャンセル', key='Cancel', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')]
    else:
        center = [
            sg.Column([[
                sg.Text(row, background_color=color, text_color='#000000', pad=((0, 0), (0, 0)), font=('', 16))]
                for row in cols[i]], element_justification=aligns[i], background_color=color)
            for i in range(0, len(cols))]
        btn = [sg.Button('OK', key='OK', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')]

    window = sg.Window(title, keep_on_top=True, modal=True, background_color=color,
                       icon=(os.getcwd() + cst.ICON_FILE), return_keyboard_events=True, element_justification='c',
                       layout=[
                           [sg.Text(msg, background_color=color, text_color='#000000', font=('', 16),
                                    pad=((20, 20), (10, 10)))], center, btn])

    while True:
        if 'Mac' == cst.PC:
            event, values = window.read(timeout=0)
        else:
            event, values = window.read()

        # 全チェック外し
        if 'check_out' == event:
            [[window[row].update(False) for row in cols[i]] for i in range(0, len(cols))]

        elif event in ['Start']:

            # チェックなしでは進めない
            is_check = False
            for i in range(0, len(cols)):
                for k in range(0, len(cols[i])):
                    if values[cols[i][k]]:
                        is_check = True
            if not is_check:
                continue

            window.close()
            return [[row for row in cols[i] if values[row]] for i in range(0, len(cols))]

        if event in [sg.WIN_CLOSED, 'OK', 'Cancel']:
            break

    window.close()
    return ''


# 進捗表示
def progress(title, bar1, bar2=None, bar3=None, interrupt=False):

    color = '#FFCCCC'
    lists = [bar1]
    if bar2 is not None:
        lists.append(bar2)
    if bar3 is not None:
        lists.append(bar3)

    layout = [
        [sg.Text(title, background_color=color, text_color='#000000', font=('', 16), pad=((10, 10), (20, 10)))], [[
            [sg.Text(bar[0], key=bar[0], background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (5, 5)))],
            [sg.ProgressBar(key=bar[0] + '_', max_value=bar[1], bar_color='#008000', size=(30, 20), pad=((15, 15), (5, 5)))]]
            for bar in lists], [sg.Text('', background_color=color)]
    ]
    # 中断ボタン interrupt = (event in [sg.WIN_CLOSED, 'interrupt'])
    if interrupt:
        layout.append([sg.Button('中断', key='interrupt', font=('', 16),
                                 pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')])

    window = sg.Window(
        title, keep_on_top=True, no_titlebar=True, modal=True, element_justification='c',
        icon=(os.getcwd() + cst.ICON_FILE), background_color=color, layout=layout)

    return window


# 完了ダイアログ
def close(is_event):

    # 中断の場合、何もしない
    if is_event is None:
        return -1
    # エラーの場合、エラーダイアログ
    elif type(is_event) == list:
        dialog(is_event[0], is_event[1], is_event[2])
        return 1

    # 正常終了の場合、完了ダイアログ
    else:
        dialog('[' + is_event + ']が完了しました。', '正常終了')
        return 0
