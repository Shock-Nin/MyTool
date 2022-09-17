#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import json
import glob
import datetime
import pandas as pd
import PySimpleGUI as sg

from business.batch.anomaly import Anomaly

PATH = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender/anomaly')
DAYWEEKS = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']


class AnomalyWeb:

    def __init__(self, function):
        self.function = function

    def do(self):

        if 'tweet' == self.function:
            Anomaly(self.function).tweet()
            return

        getattr(self, '_' + self.function)()

    # Webコンテンツ作成
    def _contents(self):

        if com.question('WEBコンテンツ作成 開始しますか？', '開始確認') <= 0:
            return

        err_msg = self._edit_anomaly()
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        err_msg = self._edit_gotobe()
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        # err_msg = self._edit_shakai_mado()
        # if err_msg is None:
        #     return
        # elif len(err_msg):
        #     com.dialog(err_msg, 'エラー発生', lv='W')
        #     return

        com.dialog('WEBコンテンツ作成 完了しました。', 'コンテンツ作成完了')

    # 通常アノマリ〜のコンテンツデータ作成
    def _edit_anomaly(self):
        files = glob.glob(PATH + '/judge/D1_*.js')

        window = com.progress('WEB(アノマリ〜)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0
        try:
            for i in range(0, len(files)):
                data = open(files[i], 'r').read().split('\n')
                cur = files[i].replace('\\', '/').split('/')[-1].split('_')[1]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                for k in range(0, len(data)):
                    pass

                # with open(PATH + '/content/H1_' + cur + '_Anomaly.js', 'w') as out:
                #     out.write('const H1_' + cur + '_GTB =\n' + json.dumps('', ensure_ascii=False, indent=4))

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + '完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

        except Exception as e:
            return 'エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass
        return ''

    # ゴトー日のコンテンツデータ作成
    def _edit_gotobe(self):
        files = glob.glob(PATH + '/special/H1_*_GTB.js')

        window = com.progress('WEB(ゴトー日)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        data = pd.read_json(files[0]).to_dict()
        hours = []

        # データの取得時間範囲を定義
        for yy in data:
            for mm in data[yy]:
                for dd in data[yy][mm]:
                    for hh in data[yy][mm][dd]:
                        hours.append(hh)
                    break
                break
            break

        total_time = 0
        try:
            jsons = []
            for i in range(0, len(files)):
                data = pd.read_json(files[i]).to_dict()
                cur = files[i].replace('\\', '/').split('/')[-1].split('_')[1]
                is_usd = (cur.startswith('USD'))

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                datas = []
                no_data_msg = ''

                # 基本データの計算
                for yy in data:
                    mm_data = {str(mm): {} for mm in range(1, 13)}

                    for mm in data[yy]:
                        wk_data = {str(wk): {} for wk in range(0, 6)}

                        for dd in data[yy][mm]:
                            week_num = datetime.date(int(yy), int(mm), int(dd)).weekday() + 1

                            vals = {str(int(hour)): {
                                'win': 0.0, 'lose': 0.0, 'win_cnt': 0, 'lose_cnt': 0}
                                for hour in hours + (['-1'] if 1 == week_num else []) if 21 < int(hour) or int(hour) < 3}

                            no_data = ''
                            try:
                                yesterday = float(data[yy][mm][dd]['-1']['Close'])
                            except:
                                no_data += 'Before, '
                            try:
                                price = float(data[yy][mm][dd]['01']['Open'])
                            except:
                                no_data += '01, '
                            try:
                                close = float(data[yy][mm][dd]['04']['Close'])
                            except:
                                no_data += '04, '

                            if 0 < len(no_data):
                                no_data_msg += ', (' + str(yy) + '-' + str(mm) + '-' + str(dd) + ') ' + no_data[:-2]
                                continue

                            price = (price if 1 == week_num else (999999.99 if is_usd else 0.0))

                            for hh in data[yy][mm][dd]:
                                hour = '99'

                                if 1 == week_num:
                                    if 1 == int(hh):
                                        hour = '-1'

                                        try:
                                            start_monday = float(data[yy][mm][dd]['00']['Open'])
                                        except:
                                            start_monday = float(data[yy][mm][dd]['01']['Open'])

                                        if is_usd:
                                            if float(data[yy][mm][dd]['01']['Close']) < start_monday:
                                                yesterday = 0
                                        else:
                                            if start_monday < float(data[yy][mm][dd]['01']['Close']):
                                                yesterday = 0

                                        if 0 == yesterday:
                                            continue

                                elif 21 < int(hh) or int(hh) < 3:

                                    # prm1 = data[yy][mm][dd][str(int(hh) - 1)]
                                    hour = str(int(hh))

                                    price = float(data[yy][mm][dd][hh]['Close'])

                                if 99 == int(hour):
                                    continue

                                close_val = (close - price if is_usd else price - close) / close * 100

                                if 0 < close_val:
                                    vals[hour]['win'] += close_val
                                    vals[hour]['win_cnt'] += 1
                                else:
                                    vals[hour]['lose'] += close_val
                                    vals[hour]['lose_cnt'] += 1

                            wk_data[str(week_num)] = vals
                        mm_data[str(int(mm))] = wk_data
                    datas.append(mm_data)

                if 0 < len(no_data_msg):
                    com.log(cur + ' None' + no_data_msg)

                # 合計エリアのデータ作成
                month_data = {str(mm): {str(wk): {str(int(hour)): {
                    'win': 0.0, 'lose': 0.0, 'win_cnt': 0, 'lose_cnt': 0, 'win_avg': 0.0, 'lose_avg': 0.0,
                    'rate': 0.0, 'ratio': 0.0, 'pf': 0}
                    for hour in ['-99'] + hours + (['-1'] if 1 == wk else []) if 21 < int(hour) or int(hour) < 3}
                    for wk in range(0, 6)} for mm in range(0, 13)}

                # データの集計
                for years in datas:
                    for mm in years:
                        for wk in years[mm]:
                            for hh in years[mm][wk]:
                                for key in years[mm][wk][hh]:

                                    month_info = ['0', mm]
                                    week_info = ['0', wk]
                                    hour_info = ['-99', hh]

                                    for mn in month_info:
                                        for wn in week_info:
                                            for hn in hour_info:
                                                month_data[mn][wn][hn][key] += years[mm][wk][hh][key]

                # 集計データの計算
                trade_info = ['win', 'lose']
                for mm in month_data:
                    for wk in month_data[mm]:
                        for hh in month_data[mm][wk]:

                            month_info = ['0', mm]
                            week_info = ['0', wk]
                            hour_info = ['-99', hh]

                            for mn in month_info:
                                for wn in week_info:
                                    for hn in hour_info:

                                        vals = month_data[mn][wn][hn]
                                        month_data[mn][wn][hn]['pf'] = \
                                            ('-' if 0 == vals['lose'] else vals['win'] / -vals['lose'])

                                        total = (vals['win_cnt'] + vals['lose_cnt'])
                                        val = (0 if 0 == total else vals['win_cnt'] / total) * 100
                                        month_data[mn][wn][hn]['rate'] = val

                                        for trade in trade_info:
                                            count = (vals[('win' if 'win' == trade else 'lose') + '_cnt'])
                                            val = (0 if 0 == count else month_data[mn][wn][hn][trade] / count)
                                            month_data[mn][wn][hn][trade + '_avg'] = val

                                        month_data[mn][wn][hn]['ratio'] = ('-' if 0 == vals['lose'] else
                                            month_data[mn][wn][hn]['win_avg'] / -month_data[mn][wn][hn]['lose_avg'])

                # 出力データの文字整形
                for mm in month_data:
                    for wk in month_data[mm]:
                        for hh in list(month_data[mm][wk]):

                            if 0 == month_data[mm][wk][hh]['win_cnt'] + month_data[mm][wk][hh]['lose_cnt']:
                                del month_data[mm][wk][hh]
                                continue

                            for key in list(month_data[mm][wk][hh]):
                                if '-99' == hh and key in ['win', 'lose', 'win_cnt', 'lose_cnt']:
                                    del month_data[mm][wk][hh][key]
                                    continue

                                if '-' == month_data[mm][wk][hh][key]:
                                    continue

                                month_data[mm][wk][hh][key] = \
                                    ('{:.' + ('0' if 0 <= key.find('_cnt') else '3') +
                                     'f}').format(float(month_data[mm][wk][hh][key]))
                                month_data[mm][wk][hh][key] = \
                                    ('0' if '0.000' == month_data[mm][wk][hh][key] else
                                     month_data[mm][wk][hh][key])

                                if float(month_data[mm][wk][hh][key]) == 0 <= key.find('_cnt'):
                                    for col in ['', '_cnt', '_avg']:
                                        month_data[mm][wk][hh][key.split('_cnt')[0] + col] = '-'

                jsons.append('"' + cur + '": ' + json.dumps(month_data, ensure_ascii=False, indent=4))
                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + '完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

            with open(PATH + '/content/GoToBe.js', 'w') as out:
                out.write('{' + ", ".join([cur_data for cur_data in jsons]) + '}')

        except Exception as e:
            return 'エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass
        return ''

    # マド空けのコンテンツデータ作成
    def _edit_shakai_mado(self):
        files = glob.glob(PATH + 'special/H1_*_GTB.csv')

        window = com.progress('WEB(マド空け)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0
        try:
            for i in range(0, len(files)):
                data = open(files[i], 'r').read().split('\n')
                cur = files[i].replace('\\', '/').split('/')[-1].split('_')[1]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                for k in range(0, len(data)):



                    pass

                with open(PATH + '/content/H1_' + cur + '_ShakaiMado.js', 'w') as out:
                    out.write('const H1_' + cur + '_GTB =\n' + json.dumps('', ensure_ascii=False, indent=4))

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + '完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))
    #
    #     except Exception as e:
    #         return 'エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass
        return ''

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False