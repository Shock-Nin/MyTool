#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import os
import shutil
import pandas as pd

LIST_HEADER = ['総数', '勝率', '勝', '敗', 'PF', 'DD',
               '平均<br>年率', '最大<br>年率', '最低<br>年率', '名前',
               '平均<br>利益', '最大<br>利益', '期待値', '平均<br>損失', '最大<br>損失',
               '現行', '推奨', '勝率<br>50', 'DD<br>10', '損失<br>3']


class EaEditUnit:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        # 個別テストのHTMLスリム化
        is_end = _slim_html()
        if 0 < len(is_end):
            return com.close(is_end)

        # 個別テストの集計リスト作成
        is_end = _edit_unit_list()
        if 0 < len(is_end):
            return com.close(is_end)

        return com.close(self.myjob)


# 個別テストのHTMLスリム化
def _slim_html():

    tests = _sort_paths(False)

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
                        outpath = cst.TEST_OUT_PATH[cst.PC] + targets[-2] + '/' + targets[-1].lower()

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

    tests = _sort_paths(True)

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
                    # HTMLのヘッダー部から取得
                    datas = open(tests[i][k], 'r').read()

                    # 名前
                    ea_name = datas[datas.find('Comments'): datas.find('TradeMargin')]
                    ea_name = ea_name[ea_name.find('=') + 2: ea_name.find(';') - 1]

                    # 初期資金
                    balance_start = datas[datas.find('初期証拠金'): datas.find('スプレッド')]
                    balance_start = balance_start[balance_start.find('right'):]
                    balance_start = float(balance_start[balance_start.find('>') + 1: balance_start.find('<')])

                    # 最大ドローダウン
                    dd_max = datas[datas.find('最大ドローダウン'): datas.find('相対ドローダウン')]
                    dd_max = dd_max[dd_max.find('right'):]
                    dd_max = float(dd_max[dd_max.find('>') + 1: dd_max.find(' (')])

                    # Risk
                    if 0 <= tests[i][k].find('Unit'):
                        risk = datas[datas.find('Risk'): datas.find('Safety')]
                        risk = float(risk[risk.find('=') + 1: risk.find(';')])

                    # HTMLの時系列データを取得
                    datas = pd.read_html(tests[i][k], encoding=('cp932' if 'Win' == cst.PC else 'utf8'),
                                         header=0, na_values=0)[1]

                    lot = 0.0
                    trade = 0
                    win = 0
                    lose = 0

                    prf_total = 0.0
                    prf_max = 0.0

                    loss_total = 0.0
                    loss_max = 0.0

                    last_year = ''
                    last_balance = 0.0
                    balance_max = 0.0
                    prf_annuals = []

                    for n in range(0, len(datas)):

                        if str(datas.at[n, '取引種別']) in ['buy', 'sell']:
                            trade += 1
                        else:
                            lot = max(lot, datas.at[n, '数量'])

                            # 年率計算用
                            if last_year != datas.at[n, '時間'][:4]:
                                last_year = datas.at[n, '時間'][:4]

                                if last_balance != datas.at[n, '残高']:
                                    if 0 < last_balance:
                                        prf_annuals.append(datas.at[n, '残高'] - last_balance)

                                    last_balance = datas.at[n, '残高']

                            # 利益計算用
                            if 0 < datas.at[n, '損益']:
                                win += 1
                                prf_total += datas.at[n, '損益']
                                prf_max = max(prf_max, datas.at[n, '損益'])
                                balance_max = max(balance_max, datas.at[n, '残高'])

                            # 損失計算用
                            elif datas.at[n, '損益'] < 0:
                                lose += 1
                                loss_total += -datas.at[n, '損益']
                                loss_max = max(loss_max, -datas.at[n, '損益'])

                    # 名前と表示クラスの定義
                    ea_name = (ea_name if 1 == len(cst.EA_PATHS[ea_name.split('_')[0]]) else targets[-1].split('.')[0])
                    ea_class = ('ea_all' if 0 <= ea_name.find('Full') or 0 <= ea_name.find('Best') else 'prm')

                    # 推奨ロット計算と、必要なアイテムの計算
                    lot = lot / (balance_start / 10000)
                    winrate = win / trade * 100
                    ddown = dd_max / balance_start * 100
                    loss1 = loss_max / balance_start * 100
                    best, win50, dd10, loss3 = _calucu_lot(lot, winrate, ddown, loss1)

                    # Fullは「Risk」100%
                    if 0 <= ea_name.find('Full'):
                        lot = risk
                        best = 0
                        win50 = 0
                        dd10 = 0
                        loss3 = 0
                    # Bestは「Risk」を計算
                    elif 0 <= ea_name.find('Best'):
                        lot = risk
                        best = 10 / (ddown / risk)
                        win50 = 0
                        dd10 = 0
                        loss3 = 0

                    html_row += '<tr>'

                    # 総数, 勝率
                    html_row += '<td class="' + ea_class + '" align="right">' + str(trade) + '</td>'
                    alert = (' warning' if winrate < 50 else ' good' if 60 < winrate else '')
                    html_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(winrate, '.2f')) + '%</td>'

                    # 勝, 敗
                    html_row += '<td class="' + ea_class + ' good" align="right">' + str(win) + '</td>'
                    html_row += '<td class="' + ea_class + ' warning" align="right">' + str(lose) + '</td>'

                    # PF, DD
                    alert = (' warning' if prf_total / loss_total < 1.3 else ' good' if 1.7 < prf_total / loss_total else '')
                    html_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(prf_total / loss_total, '.2f')) + '</td>'
                    alert = (' alert' if 10 <= ddown and ea_name.find('Full') < 0 else '')
                    html_row += '<td class="dd ' + ea_class + alert + '" align="right">' + str(format(ddown, '.2f')) + '%</td>'

                    # 平均年率, 最大年率, 最低年率
                    html_row += '<td class="' + ea_class + '" align="right">' + str(format((sum(prf_annuals) / len(prf_annuals)) / balance_start * 100, '.2f')) + '%</td>'
                    html_row += '<td class="' + ea_class + '" align="right">' + str(format(max(prf_annuals)/ balance_start * 100, '.2f')) + '%</td>'
                    alert = (' warning' if min(prf_annuals) <= 0 else '')
                    html_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(min(prf_annuals) / balance_start * 100, '.2f')) + '%</td>'

                    # 名前とリンクの作成
                    html_row += '<td class="' + ('ea_all' if 0 <= ea_name.find('Full') or 0 <= ea_name.find('Best') else 'ea_row')
                    html_row += '" align="left"><a href="http://' + cst.DEV_IP + '/test/'
                    html_row += targets[-2] + '/' + ea_name.lower() + '.htm" target="_blank">' + ea_name + '</a></td>'

                    # 平均利益, 最大利益
                    html_row += '<td class="' + ea_class + '" align="right">' + str(format((prf_total / win) / balance_start * 100, '.2f')) + '%</td>'
                    html_row += '<td class="' + ea_class + '" align="right">' + str(format(prf_max / balance_start * 100, '.2f')) + '%</td>'

                    # 期待値
                    alert = (' warning' if ((prf_total - loss_total) / trade) / balance_start * 100 < 0.1 else
                             ' good' if 0.3 < ((prf_total - loss_total) / trade) / balance_start * 100 else '')
                    html_row += '<td class="' + ea_class + alert + '" align="right">' + \
                                str(format(((prf_total - loss_total) / trade) / balance_start * 100, '.2f')) + '%</td>'

                    # 平均損失, 最大損失
                    html_row += '<td class="' + ea_class + ' warning" align="right">' + str(format((loss_total / lose) / balance_start * 100, '.2f')) + '%</td>'
                    alert = (' alert' if 3 <= loss1 else ' warning')
                    html_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(loss1, '.2f')) + '%</td>'

                    # 現行, 推奨
                    is_full = (0 <= ea_name.find('Full') or 0 <= ea_name.find('Best'))

                    alert = (('' if str(format(best, '.2f')) == str(format(lot, '.2f')) else ' alert'
                             if best < lot else ' good' if lot < best else '')
                             if ea_name.find('Full') < 0 else '')
                    html_row += '<td class="' + ea_class + alert + '" align="right">'
                    html_row += str(format(lot, '.0f' if is_full else '.2f')) + '</td>'
                    if 0 <= ea_name.find('Full'):
                        html_row += '<td class="' + ea_class + '"></td>'
                    else:
                        html_row += '<td class="' + ea_class + '" align="right">'
                        html_row += str(format(best, '.0f' if is_full else '.2f')) + '</td>'

                    # 勝率50, DD10, 損失3
                    if is_full:
                        html_row += "".join(['<td class="' + ea_class + '">' for _ in range(3)])
                    else:
                        html_row += '<td class="' + ea_class + '" align="right">' + str(format(win50, '.2f')) + '</td>'
                        html_row += '<td class="' + ea_class + '" align="right">' + str(format(dd10, '.2f')) + '</td>'
                        html_row += '<td class="' + ea_class + '" align="right">' + str(format(loss3, '.2f')) + '</td>'

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
    outpath = cst.DATA_PATH[cst.PC] + 'Unit.html'
    with open(outpath, 'w') as outfile:

        # HTMLヘッダー
        html = '<html><head><title>EA個別成績</title>'
        html += '</head><body><div align="center">'
        html += '<table><tr><td class="title col" align="center">EA個別成績</td></tr><tr><td>'
        html += '<table cellspacing="0" cellpadding="0"><tr align="center">'
        html += "".join(['<td class="col">' + col + '</td>' for col in LIST_HEADER]) + '</tr>'

        html += html_data

        # HTMLフッター(スタイル)
        html += '</table></td></tr></table></div><style type="text/css">'
        html += '.title    {font-size: 24px;}'
        html += '.col      {border: 1px solid #DDDDDD; padding: 5px 15px; background: #FFFFAA;}'
        html += '.ea_row   {border: 1px solid #DDDDDD; padding: 5px 10px; background: #FFFFFF;}'
        html += '.ea_all   {border: 1px solid #DDDDDD; padding: 5px 10px; background: #CCFFCC;}'
        html += '.prm      {border: 1px solid #DDDDDD; padding: 5px 10px;}'
        html += '.dd       {color: #FF00FF;}'
        html += '.good     {color: #0000FF;}'
        html += '.warning  {color: #FF0000;}'
        html += '.alert    {background: #FF0000; color: #FFFFFF;}'
        html += '.up_line  {border-top: 2px solid #000000;}'
        html += '</style></body></html>'

        outfile.write(html)

    com.log('ファイル作成: ' + outpath)
    return []


# 推奨ロットの計算
def _calucu_lot(lot, winrate, ddown, loss1):

    win50 = lot * ((100 - (50 - winrate)) if winrate < 50 else (100 + (winrate - 50))) / 100
    dd10 = 0.1 / (ddown / 100) * lot
    loss3 = 0.03 / (loss1 / 100) * lot
    best = min(win50, dd10, loss3)

    return best, win50, dd10, loss3


# リアルパスを規則順ソートで格納
def _sort_paths(is_out):

    paths = []
    get_paths = os.listdir(cst.TEST_UNIT[cst.PC])

    for key1 in cst.CURRNCYS_EA:
        for key2 in cst.EA_PATHS:

            for get_path in get_paths:

                if 1 == len(cst.EA_PATHS[key2]):
                    is_key = (get_path == cst.EA_PATHS[key2][0])
                    path = cst.TEST_UNIT[cst.PC] + cst.EA_PATHS[key2][0]
                else:
                    is_key = (get_path == cst.EA_PATHS[key2][1] + key1)
                    path = cst.TEST_UNIT[cst.PC] + cst.EA_PATHS[key2][1] + key1

                # 並び順でなければパス
                if not is_key:
                    continue

                get_files = os.listdir(path)
                get_files.sort()
                files = []

                for get_file in get_files:
                    if 0 <= get_file.find(key1) and 0 <= get_file.find('.htm'):
                        files.append(path.replace(cst.TEST_UNIT[cst.PC], cst.TEST_OUT_PATH[cst.PC]
                                     if is_out else cst.TEST_UNIT[cst.PC]) + '/' + get_file)

                paths.append(files)
    return paths
