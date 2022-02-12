#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import shutil

from common import com
from const import cst

import os
import pandas as pd

LIST_HEADER = ['名前', '総数', '勝率', '勝', '敗', 'PF', 'DD',
               '平均\n年率', '最大\n年率', '最低\n年率', '平均\n損失', '最大\n損失',
               '現行', '推奨', '期待値', '勝率50', 'DD10', '損失3']


class EaEditUnit:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        # # 個別テストのHTMLスリム化
        # is_end = _slim_html()
        # if 0 < len(is_end):
        #     return com.close(is_end)

        # 個別テストの集計リスト作成
        is_end = _edit_unit_list()
        if 0 < len(is_end):
            return com.close(is_end)

        return com.close(self.myjob)


# 個別テストのHTMLスリム化
def _slim_html():

    # 対象ファイルのパスリスト作成
    tests = []
    paths = os.listdir(cst.TEST_UNIT[cst.PC])
    for path in paths:

        # フォルダでなければパス
        if not os.path.isdir(cst.TEST_UNIT[cst.PC] + '/' + path):
            continue

        files = os.listdir(cst.TEST_UNIT[cst.PC] + '/' + path)
        test = []

        # .htmファイルのみ、パスを格納
        for file in files:
            if 0 <= file.find('.htm'):
                test.append(cst.TEST_UNIT[cst.PC] + '/' + path + '/' + file)
        tests.append(test)

    # HTMLを整形して、公開パスに出力
    err_msg = ''
    try:
        for i in range(0, len(tests)):
            for k in range(0, len(tests[i])):
                targets = tests[i][k].split('/')

                # 進捗表示
                if 0 == i + k:
                    bar1 = targets[-2]
                    bar2 = targets[-1].split('.')[0]
                    window = com.progress('1. HTML整形中', [bar1, len(tests)], [bar2, len(tests[i])])
                    window.read(timeout=0)

                window[bar1].update(targets[-2] + '(' + str(i) + ' / ' + str(len(tests)) + ')')
                window[bar2].update(targets[-1].split('.')[0] + '(' + str(k) + ' / ' + str(len(tests[i])) + ')')
                window[bar1 + '_'].Update(i)
                window[bar2 + '_'].update(k)

                try:
                    # テストHTMLを開く
                    with open(tests[i][k], 'r', encoding='cp932') as infile:
                        outpath = cst.TEST_OUT_PATH[cst.PC] + '/' + targets[-2] + '/' + targets[-1].lower()

                        with open(outpath, 'w') as outfile:
                            infile = infile.read()

                            # 余計な区切り文字を除去
                            infile = infile.replace('===', '').replace('---', '').replace('___', '')
                            # パラメータの列幅調整
                            infile = infile.replace('>Comments', ' width="300">Comments')

                            for data in infile.split('\n'):

                                # 時系列から「modify」を除外
                                if 0 <= data.find('modify'):
                                    continue

                                # パラメータから「Logic*」を除外
                                while 0 <= data.find('Logic'):
                                    data = data[:data.find('Logic')] + \
                                           data[data.find('Logic') + data[data.find('Logic'):].find(';') + 1:]

                                # 必要な箇所のみ書き出し
                                outfile.write(data + '\n')

                    # 画像をコピー
                    shutil.copy2(tests[i][k].replace('.htm', '.gif'), outpath.replace('.htm', '.gif'))

                except Exception as e:
                    err_msg += '\n　' + targets[-2] + '/' + targets[-1] + '\n　　' + str(e)
                    com.log(str(e))
    finally:
        try: window.close()
        except: pass

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    return []


# 個別テストの集計リスト作成
def _edit_unit_list():

    # 新ファイルのパスリスト作成
    tests = []
    paths = os.listdir(cst.TEST_UNIT[cst.PC])
    paths.sort(reverse=False)

    for path in paths:

        # フォルダでなければパス
        if not os.path.isdir(cst.TEST_UNIT[cst.PC] + path):
            continue

        files = os.listdir(cst.TEST_UNIT[cst.PC].replace(cst.TEST_UNIT[cst.PC], cst.TEST_OUT_PATH[cst.PC]) + path)
        test = []

        # .htmファイルのみ、パスを格納
        for file in files:
            if 0 <= file.find('.htm'):
                test.append(cst.TEST_OUT_PATH[cst.PC] + path + '/' + file)

        test.sort(reverse=False)
        tests.append(test)

    # HTMLの時系列データから集計
    html_data = ''
    err_msg = ''
    try:
        for i in range(0, len(tests)):
            html_row = ''

            for k in range(0, len(tests[i])):
                targets = tests[i][k].split('/')

                # 進捗表示
                if 0 == i + k:
                    bar1 = targets[-2]
                    bar2 = targets[-1].split('.')[0]
                    window = com.progress('2. 集計データ作成中', [bar1, len(tests)], [bar2, len(tests[i])])
                    window.read(timeout=0)

                window[bar1].update(targets[-2] + '(' + str(i) + ' / ' + str(len(tests)) + ')')
                window[bar2].update(targets[-1].split('.')[0] + '(' + str(k) + ' / ' + str(len(tests[i])) + ')')
                window[bar1 + '_'].Update(i)
                window[bar2 + '_'].Update(k)

                try:
                    # HTMLの時系列データを取得
                    file = pd.read_html(tests[i][k], encoding='cp932', header=0, na_values=0)
                    ea_name = str(file[0])
                    ea_name = ea_name[ea_name.find('Comments'): ea_name.find('TradeMargin')]
                    ea_name = ea_name[ea_name.find('=') + 2: ea_name.find(';') - 1]

                    datas = file[1]

                    trade = 0
                    win = 0
                    lose = 0
                    dd_max = 0.0
                    lastyear = 0
                    balance_yearend = []
                    prf_total = 0.0
                    prf_max = 0.0
                    prf_annuals = []
                    prf_annual_avg = 0.0
                    prf_annual_max = 0.0
                    prf_annual_min = 0.0
                    losses = []
                    loss_total = 0.0
                    loss_max = 0.0
                    loss_avg = 0.0

                    ea_name = (ea_name if 0 == i else targets[-1].split('.')[0])

                    html_row += '<tr><td class="row"><a href="http://' + cst.DEV_IP + '/test/'
                    html_row += targets[-2] + '/' + ea_name.lower() + '.htm" target="_blank">' + ea_name + '</a></td>'
                    for n in range(0, len(datas)):

                        if str(datas.at[n, '取引種別']) in ['buy', 'sell']:
                            trade += 1
                        else:
                            if 0 < datas.at[n, '損益']:
                                win += 1
                                prf_total += datas.at[n, '損益']
                                prf_max = max(prf_max, datas.at[n, '残高'])

                            elif datas.at[n, '損益'] < 0:
                                lose += 1
                                loss_total += datas.at[n, '損益']
                                if 0 < prf_max:
                                    dd_max = max(dd_max, (prf_max - datas.at[n, '残高']) / prf_max)

                    # 総数, 勝率, 勝, 敗, PF, DD
                    html_row += '<td class="prm">' + str(trade) + '</td>'
                    html_row += '<td class="prm">' + str(format(win / trade * 100, '.2f')) + '%</td>'
                    html_row += '<td class="prm">' + str(win) + '</td>'
                    html_row += '<td class="prm">' + str(lose) + '</td>'
                    html_row += '<td class="prm">' + str(format(prf_total / -loss_total, '.2f')) + '</td>'
                    html_row += '<td class="prm">' + str(format(dd_max * 100, '.2f')) + '%</td>'

                    # 平均年率, 最大年率, 最低年率, 平均損失, 最大損失,
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'

                    # 現行, 推奨, 期待値, 勝率50, DD10, 損失3
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'
                    html_row += '<td class="prm">' + str() + '</td>'

                except Exception as e:
                    err_msg += '\n　' + targets[-2] + '/' + targets[-1] + '\n　　' + str(e)
                    com.log(str(e))

            html_data += html_row + '</tr>'
    finally:
        try: window.close()
        except: pass

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    # HTML書き出し
    outpath = cst.DATA_PATH[cst.PC] + '/Unit.html'
    with open(outpath, 'w') as outfile:

        # HTMLヘッダー
        html = '<html><head><title>EA個別成績</title>'
        html += '</head><body><div align="center">'
        html += '<table><tr><td class="eaName" align="center">EA個別成績</td></tr><tr><td>'
        html += '<table cellspacing="0" cellpadding="0"><tr>'
        html += "".join(['<td class="col">' + col + '</td>' for col in LIST_HEADER]) + '</tr>'

        html += html_data

        # HTMLフッター(スタイル)
        html += '</table></td></tr></table></div><style type="text/css">'
        html += '.title    {padding: 10px; background: #FFCCFF; font-size: 24px;}'
        html += '.col      {border: 1px solid #DDDDDD; padding: 5px 15px; background: #FFFFAA;}'
        html += '.row      {border: 1px solid #DDDDDD; padding: 5px 15px; background: #CCFFFF;}'
        html += '.prm      {border: 1px solid #DDDDDD; padding: 5px 10px;}'
        html += '.zero     {background: #EEEEEE; color: #AAAAAA;}'
        html += '.up_line  {border-top: 2px solid #000000;}'
        html += '</style></body></html>'

        outfile.write(html)

    return []


# 適正ロットの算出
def _calcu_lot():


    return []


# CSVファイルからHTML化
def _output_html():


    return []
