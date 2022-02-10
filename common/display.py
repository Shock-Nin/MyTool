#!/usr/bin/env python
# -*- coding: utf-8 -*-

import PySimpleGUI as sg


# 標準ダイアログをレベルに応じて表示
def dialog(msg, title, lv=''):

    color = '#FF7777' if 'E' == lv else 'FFFF77' if 'W' == lv else '#77CCFF'
    window = sg.Window(title, keep_on_top=True, modal=True, background_color=color, element_justification='c', layout=[
        [sg.Text(msg, background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (20, 10)))],
        [sg.Button('OK', key='OK', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')]])

    while True:
        event, values = window.read()
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
        event, values = window.read()
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

    color = '#FF7777'
    bars = [[sg.Text(bar1[0], background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (20, 10)))],
            [sg.ProgressBar(max_value=bar1[1], bar_color='008000', pad=((20, 20), (10, 10)))]]

    window = sg.Window(title, keep_on_top=True, no_titlebar=True, modal=True,
                       background_color=color, element_justification='c', layout=[
        [sg.Text(title, background_color=color, text_color='#000000', font=('', 16), pad=((20, 20), (20, 10)))],
        bars,
        [sg.Button('中断', key='中断', font=('', 16), pad=((10, 10), (10, 20)), size=(10, 1), button_color='#777777')]])

    return window


# progressの中断イベント
def interrupt(window):
    end = False
    flg = question('中断しますか？', '継続？中断？')
    if 0 < flg:
        end = True
        window.close()
    return end
