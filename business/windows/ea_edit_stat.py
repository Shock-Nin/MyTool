#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

from business. windows import ea_edits as inheritance

import pandas as pd

IN_PATH = cst.TEST_OUT_PATH[cst.PC] + 'Merge/'
NAME_FILE = cst.DATA_PATH[cst.PC] + 'Unit.html'

OUT_NAMES = ['成績', '年率']
OUT_FILES = ['Total', 'Years']
OUT_HEADERS = [
    ['総数', '勝率', '勝', '敗', 'PF', 'DD', '月<br>頻度', '年勝率',
     '平均<br>年率', '最大<br>年率', '最低<br>年率', '期待値'],
    ['年率', '総数', '勝率', '勝', '敗']]


class EaEditStat:

    def do(self):

        # 個別テストの集計リスト作成
        is_end = _edit_stat_status()
        if 0 < len(is_end):
            return com.close(is_end)

        return 0


# 個別テストの集計リスト作成
def _edit_stat_status():

    name_list = inheritance.name_list(NAME_FILE)
    if name_list is None:
        return ['以下のファイルでエラーが発生しました。\n　' + NAME_FILE, '読み込みエラー', 'E']

    name_list.append('All')
    err_msg = ''

    # HTMLの時系列データから集計
    total_row = ''
    years_row = ''
    try:
        for i in range(0, len(name_list)):

            targets = cst.TEST_OUT_PATH[cst.PC] + 'Merge/' + name_list[i].lower() + '.htm'

            # 進捗表示
            if 0 == i:
                bar1 = name_list[i] + '(' + str(i) + ' / ' + str(len(name_list)) + ')'
                window = com.progress('4. 統合データ作成中', [bar1, len(name_list)])
                window.read(timeout=0)

            window[bar1].update(name_list[i] + '(' + str(i) + ' / ' + str(len(name_list)) + ')')
            window[bar1 + '_'].Update(i)

            try:
                # HTMLのヘッダー部から取得
                datas = open(targets, 'r').read()

                # 初期資金
                balance_start = datas[datas.find('Initial deposit'):]
                balance_start = balance_start[balance_start.find('right'):]
                balance_start = float(balance_start[balance_start.find('>') + 1: balance_start.find('<')])

                # 最大ドローダウン
                dd_max = datas[datas.find('Maximal drawdown'): datas.find('Relative drawdown')]
                dd_max = dd_max[dd_max.find('right'):]
                dd_max = float(dd_max[dd_max.find('>') + 1: dd_max.find(' (')])

                # 連勝
                win_max = datas[datas.find('consecutive wins'): datas.find('consecutive losses (loss in money)')]
                win_max = win_max[win_max.find('right'):]
                win_max = win_max[win_max.find('>') + 1: win_max.find(' (')]

                # 連敗
                lose_max = datas[datas.find('consecutive losses'): datas.find('consecutive loss (count of losses)')]
                lose_max = lose_max[lose_max.find('right'):]
                lose_max = lose_max[lose_max.find('>') + 1: lose_max.find(' (')]

                # HTMLの時系列データを取得
                datas = pd.read_html(targets, encoding=('cp932' if 'Win' == cst.PC else 'utf8'),
                                     header=0, na_values=0)[1]

                lot = 0.0
                win = 0
                lose = 0

                prf_total = 0.0
                prf_max = 0.0

                loss_total = 0.0
                loss_max = 0.0

                last_balance = 0.0
                balance_max = 0.0
                prf_annuals = []

                year_count = 0
                year_win = 0
                year_lose = 0

                # 年率, 総数, 勝率, 勝, 敗, 連勝, 連敗
                years_annuals = []
                trade_annuals = []
                win_annuals = []
                lose_annuals = []
                start_trade = 0
                start_win = 0
                start_lose = 0

                for n in range(0, len(datas)):
                    if str(datas.at[n, 'Type']) not in ['buy', 'sell']:
                        start_year = datas.at[n, 'Time'][:4]
                        start_balance = datas.at[n, 'Balance']
                        break

                for n in range(0, len(datas)):

                    m = n
                    if m == len(datas) - 1:
                        while not 0 < datas.at[n, 'Balance']:
                            n -= 1
                        last_balance = datas.at[n, 'Balance']

                    if str(datas.at[n, 'Type']) not in ['buy', 'sell']:
                        lot = max(lot, datas.at[n, 'Size'])

                        # 年率計算用
                        if start_year != datas.at[n, 'Time'][:4] or m == len(datas) - 1:

                            year_count += 1
                            if 0 < last_balance - start_balance:
                                year_win += 1
                            else:
                                year_lose += 1

                            prf_annuals.append(last_balance - start_balance)
                            years_annuals.append(start_year)
                            trade_annuals.append((win + lose) - start_trade)
                            win_annuals.append(win - start_win)
                            lose_annuals.append(lose - start_lose)

                            start_year = datas.at[n, 'Time'][:4]
                            start_balance = datas.at[n, 'Balance']
                            start_trade = (win + lose)
                            start_win = win
                            start_lose = lose

                        # 利益計算用
                        if 0 < datas.at[n, 'Profit']:
                            win += 1
                            prf_total += datas.at[n, 'Profit']
                            prf_max = max(prf_max, datas.at[n, 'Profit'])
                            balance_max = max(balance_max, datas.at[n, 'Balance'])

                        # 損失計算用
                        elif datas.at[n, 'Profit'] < 0:
                            lose += 1
                            loss_total += -datas.at[n, 'Profit']
                            loss_max = max(loss_max, -datas.at[n, 'Profit'])

                        last_balance = datas.at[n, 'Balance']

                # 名前と表示クラスの定義
                ea_name = name_list[i]
                ea_class = ('ea_all' if 0 <= ea_name.find('Full') or 0 <= ea_name.find('Best') or 0 <= ea_name.find('All') else 'prm')
                base_tag = '<td class="' + ea_class + '" align="right">'

                if 0 == len(total_row):
                    total_row += '<td class="col">' + cst.EA_DATA_NAMES[1] + '</td>'
                    total_row += "".join(['<td class="col">' + col + '</td>' for col in OUT_HEADERS[0]]) + '</tr>'

                # 名前とリンクの作成
                total_row += '<tr><td class="' + ('ea_all' if 0 <= ea_name.find('Full') or 0 <= ea_name.find('Best') or 0 <= ea_name.find('All') else 'ea_row')
                total_row += '" align="left"><a href="' + cst.TEST_LINK[cst.PC] + 'Merge/'
                total_row += name_list[i].lower() + '.htm' + '" target="_blank">' + ea_name + '</a></td>'

                # 総数, 勝率
                winrate = win / (win + lose) * 100
                total_row += base_tag + str((win + lose)) + '</td>'
                alert = (' warning' if winrate < 50 else ' good' if 60 < winrate else '')
                total_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(winrate, '.1f')) + '%</td>'

                # 勝, 敗
                total_row += '<td class="' + ea_class + ' good" align="right">' + str(win)
                total_row += '<font color="#000000">(' + str(win_max) + ')</font></td>'
                total_row += '<td class="' + ea_class + ' warning" align="right">' + str(lose)
                total_row += '<font color="#000000">(' + str(lose_max) + ')</font></td>'

                # PF, DD
                ddown = dd_max / balance_start * 100
                alert = (' warning' if prf_total / loss_total < 1.3 else ' good' if 1.7 < prf_total / loss_total else '')
                total_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(prf_total / loss_total, '.2f')) + '</td>'
                alert = (' alert' if 20 <= ddown and ea_name.find('Full') < 0 and ea_name.find('All') < 0 else '')
                total_row += '<td class="dd ' + ea_class + alert + '" align="right">' + str(format(ddown, '.2f')) + '%</td>'

                # 月頻度, 年勝率
                total_row += base_tag + str(format((win + lose) / (year_count * 12), '.1f')) + '</td>'
                total_row += base_tag + str(int(year_win / year_count * 100)) + '%'
                total_row += ('' if 0 == year_lose else '<font color="#FF0000">,' + str(year_lose) + '</font>') + '</td>'

                # 平均年率, 最大年率, 最低年率
                total_row += base_tag + str(format((sum(prf_annuals) / len(prf_annuals)) / balance_start * 100, '.1f')) + '%</td>'
                total_row += base_tag + str(format(max(prf_annuals)/ balance_start * 100, '.1f')) + '%</td>'
                alert = (' warning' if min(prf_annuals) <= 0 else '')
                total_row += '<td class="' + ea_class + alert + '" align="right">' + str(format(min(prf_annuals) / balance_start * 100, '.1f')) + '%</td>'

                # 期待値
                alert = (' warning' if ((prf_total - loss_total) / (win + lose)) / balance_start * 100 < 0.1 else
                         ' good' if 0.3 < ((prf_total - loss_total) / (win + lose)) / balance_start * 100 else '')
                total_row += '<td class="' + ea_class + alert + '" align="right">'
                total_row += str(format(((prf_total - loss_total) / (win + lose)) / balance_start * 100, '.2f')) + '%</td>'

                # 年率
                if 0 == len(years_row):
                    # ヘッダー上段(年)
                    years_row += '<td class="col" rowspan="2">' + cst.EA_DATA_NAMES[2] + '</td>'
                    for k in reversed(range(len(years_annuals) - 3, len(years_annuals))):
                        years_row += '<td class="col year" colspan="5">' + str(years_annuals[k]) + '</td>'
                    for k in reversed(range(0, len(years_annuals) - 3)):
                        years_row += '<td class="col" rowspan="2">' + str(years_annuals[k]) + '</td>'

                    years_row += '</tr><tr align="center">'
                    # ヘッダー下段(項目)
                    for k in range(0, 3):
                        for n in range(0, len(OUT_HEADERS[1])):
                            years_row += '<td class="col year">' + OUT_HEADERS[1][n] + '</td>'

                    years_row += '</tr>'
                years_row += '<tr>'

                years_row += '<td class="' + ('ea_all' if 0 <= ea_name.find('Full') or 0 <= ea_name.find('Best') or 0 <= ea_name.find('All') else 'ea_row')
                years_row += '" align="left"><a href="' + cst.TEST_LINK[cst.PC] + 'Merge/'
                years_row += name_list[i].lower() + '.htm' + '" target="_blank">' + ea_name + '</a></td>'

                # 最新年〜前々年の、年率, 総数, 勝率, 勝, 敗
                for k in reversed(range(len(years_annuals) - 3, len(years_annuals))):
                    years_row += base_tag + str(format(prf_annuals[k] / balance_start * 100, '.1f')) + '%</td>'
                    years_row += base_tag + str(trade_annuals[k]) + '</td>'
                    years_row += base_tag + str(format(win_annuals[k] / trade_annuals[k] * 100, '.1f')) + '%</td>'
                    years_row += base_tag + str(win_annuals[k]) + '</td>'
                    years_row += base_tag + str(lose_annuals[k]) + '</td>'

                # 前々年以前の、年率
                for k in reversed(range(0, len(years_annuals) - 3)):
                    years_row += base_tag + str(format(prf_annuals[k] / balance_start * 100, '.1f')) + '%</td>'

            except Exception as e:
                err_msg += '\n　' + targets + '\n　　' + str(e)
                com.log(str(e))

        total_data = total_row + '</tr>'
        years_data = years_row + '</tr>'
    finally:
        try: window.close()
        except: pass

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    # HTML書き出し
    html_datas = [total_data, years_data]
    for i in range(0, len(OUT_NAMES)):

        outpath = cst.DATA_PATH[cst.PC] + OUT_FILES[i] + '.html'
        with open(outpath, 'w', encoding='utf8') as outfile:

            # HTMLヘッダー
            html = '<html><head><title>EA統合' + OUT_NAMES[i] + '</title>'
            html += '<meta charset="utf-8"/></head><body><div align="center">'
            html += '<table cellspacing="0" cellpadding="0"><tr align="center">'

            html += html_datas[i]

            # HTMLフッター(スタイル)
            html += '</table></div><style type="text/css">'
            html += '.col      {border: 1px solid #DDDDDD; padding: 5px 15px; background: #FFCCCC;}'
            html += '.ea_row   {border: 1px solid #DDDDDD; padding: 5px 10px; background: #FFFFFF;}'
            html += '.ea_all   {border: 1px solid #DDDDDD; padding: 5px 10px; background: #CCFFFF;}'
            html += '.prm      {border: 1px solid #DDDDDD; padding: 5px 10px;}'
            html += '.year     {background: #FF8833;}'
            html += '.dd       {color: #FF00FF;}'
            html += '.good     {color: #0000FF;}'
            html += '.warning  {color: #FF0000;}'
            html += '.alert    {background: #FF0000; color: #FFFFFF;}'
            html += '</style></body></html>'

            outfile.write(html)

        com.log('ファイル作成: ' + outpath)

    return []


