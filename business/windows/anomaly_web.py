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
            if com.question('Tweet作成 開始しますか？', '開始確認') <= 0:
                return
            Anomaly(self.function).tweet()
            return

        getattr(self, '_' + self.function)()

    # Webコンテンツ作成
    def _contents(self):

        # if com.question('WEBコンテンツ作成 開始しますか？', '開始確認') <= 0:
        #     return

        # err_msg = self._edit_anomaly()
        # if err_msg is None:
        #     return
        # elif len(err_msg):
        #     com.dialog(err_msg, 'エラー発生', lv='W')
        #     return
        #
        # err_msg = self._edit_gotobe()
        # if err_msg is None:
        #     return
        # elif len(err_msg):
        #     com.dialog(err_msg, 'エラー発生', lv='W')
        #     return

        err_msg = self._edit_shakai_mado()
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        com.dialog('WEBコンテンツ作成 完了しました。', 'コンテンツ作成完了')

    # 通常アノマリ〜のコンテンツデータ作成
    def _edit_anomaly(self):
        files = glob.glob(PATH + '/judge/D1_*.js')

        window = com.progress('WEB(アノマリ〜)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0
        try:
            jsons = []
            for i in range(0, len(files)):
                data = open(files[i], 'r').read().split('\n')
                cur = files[i].replace('\\', '/').split('/')[-1].split('_')[1]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                for k in range(0, len(data)):



                    pass

                # jsons.append('"' + cur + '": ' + json.dumps(month_data, ensure_ascii=False, indent=4))
                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + '完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

            with open(PATH + '/content/ShakaiMado.js', 'w') as out:
                out.write('{' + ", ".join([cur_data for cur_data in jsons]) + '}')

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

                        for wk in data[yy][mm]:
                            week_num = datetime.date(int(yy), int(mm), int(wk)).weekday() + 1

                            vals = {str(int(hour)): {
                                'win': 0.0, 'lose': 0.0, 'win_cnt': 0, 'lose_cnt': 0}
                                for hour in hours + (['-1'] if 1 == week_num else []) if 21 < int(hour) or int(hour) < 3}

                            no_data = ''
                            try:
                                yesterday = float(data[yy][mm][wk]['-1']['Close'])
                            except:
                                no_data += 'Before, '
                            try:
                                price = float(data[yy][mm][wk]['01']['Open'])
                            except:
                                no_data += '01, '
                            try:
                                close = float(data[yy][mm][wk]['04']['Close'])
                            except:
                                no_data += '04, '

                            if 0 < len(no_data):
                                no_data_msg += ', (' + str(yy) + '-' + str(mm) + '-' + str(wk) + ') ' + no_data[:-2]
                                continue

                            price = (price if 1 == week_num else (999999.99 if is_usd else 0.0))

                            for hh in data[yy][mm][wk]:
                                hour = '99'

                                if 1 == week_num:
                                    if 1 == int(hh):
                                        hour = '-1'

                                        try:
                                            start_monday = float(data[yy][mm][wk]['00']['Open'])
                                        except:
                                            start_monday = float(data[yy][mm][wk]['01']['Open'])

                                        if is_usd:
                                            if float(data[yy][mm][wk]['01']['Close']) < start_monday:
                                                yesterday = 0
                                        else:
                                            if start_monday < float(data[yy][mm][wk]['01']['Close']):
                                                yesterday = 0

                                        if 0 == yesterday:
                                            continue

                                elif 21 < int(hh) or int(hh) < 3:

                                    hour = str(int(hh))
                                    price = float(data[yy][mm][wk][hh]['Close'])

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

        # except Exception as e:
        #     return 'エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass
        return ''

    # マド空けのコンテンツデータ作成
    def _edit_shakai_mado(self):
        files = glob.glob(PATH + '/special/H1_*_MAD.js')

        window = com.progress('WEB(マド空け)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0
        try:
            jsons = []
            for i in range(0, len(files)):
                data = pd.read_json(files[i]).to_dict()
                cur = files[i].replace('\\', '/').split('/')[-1].split('_')[1]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                datas = []
                misses = [0.2, 0.5, 1.0]
                heights = ['total'] + misses
                comps = [['today', 'tomorrow'], [75, 100, 125]]
                no_data_msg = ''

                # 基本データの計算
                for yy in data:
                    mm_data = {str(mm): {} for mm in range(1, 13)}

                    for mm in data[yy]:
                        wk_data = {str(wk): {} for wk in range(0, 5)}

                        for wk in data[yy][mm]:

                            vals = {height: ({**{'half_keep': 0, 'half_out': 0,
                                              'up': 0.0, 'dn': 0.0, 'up_cnt': 0, 'dn_cnt': 0},
                                              **{day + str(comp): [0, {'miss' + str(miss).replace('.', ''): 0 for miss in misses}]
                                                 for day in comps[0] for comp in comps[1]}}
                                             if float == type(height) else 0) for height in heights}

                            try:
                                before = float(data[yy][mm][wk]['-1']['Before'])
                                after = float(data[yy][mm][wk]['-1']['After'])
                                start = float(data[yy][mm][wk]['-1']['Start'])
                                comp_target = float(data[yy][mm][wk]['-1']['Close'])
                            except:
                                no_data_msg += ', 金曜(' + str(yy) + '-' + str(mm) + '-' + str(wk) + ')'
                            try:
                                high = float(data[yy][mm][wk]['0']['High'])
                                low = float(data[yy][mm][wk]['0']['Low'])
                            except:
                                try:
                                    high = float(data[yy][mm][wk]['1']['High'])
                                    low = float(data[yy][mm][wk]['1']['Low'])
                                except:
                                    no_data_msg += ', 月曜(' + str(yy) + '-' + str(mm) + '-' + str(wk) + ')'
                                    continue

                            # 週明けの回数をカウント
                            vals['total'] += 1
                            if 0 < after:
                                updn = 'up'
                            elif after < 0:
                                updn = 'dn'
                            else:
                                continue

                            # マドの大きさ別で、出現回数をカウント
                            comp_heights = []
                            for height in heights:

                                if float == type(height):
                                    if height / 100 < abs(after):
                                        vals[height][updn + '_cnt'] += 1
                                        comp_heights.append(height)

                            # マドが大きさ別で成立した場合
                            for height in comp_heights:

                                # オープンから1時間後の変動
                                val = abs(start * after * 0.5)

                                if 0 < after:
                                    vals[height]['half_out'] += (1 if start + val < high else 0)
                                    vals[height]['half_keep'] += (1 if low < start - val else 0)
                                elif after < 0:
                                    vals[height]['half_keep'] += (1 if start + val < high else 0)
                                    vals[height]['half_out'] += (1 if low < start - val else 0)

                                is_misses = [False for _ in misses]
                                is_comps = [False for _ in comps[1]]

                                for k in range(0, len(comps[1])):

                                    # 高安値で、成否と成功前の失敗をカウント
                                    for hh in data[yy][mm][wk]:

                                        # totalは、何もしない
                                        if str == type(height) or -1 == int(hh):
                                            continue

                                        day = ('today' if 24 <= int(hh) else 'tomorrow')

                                        high = float(data[yy][mm][wk][hh]['High'])
                                        low = float(data[yy][mm][wk][hh]['Low'])

                                        # マドがオープンからの逆行が、埋まりより先の場合
                                        for m in range(0, len(is_misses)):
                                            if not is_misses[m] and not is_comps[1]:

                                                val = abs(comp_target * after * misses[m])
                                                if 'up' == updn:
                                                    is_misses[m] = start + val < high
                                                else:
                                                    is_misses[m] = low < start - val

                                                if is_misses[m]:
                                                    vals[height][day + str(comps[1][k])][1][
                                                        'miss' +str(misses[m]).replace('.', '')] += 1

                                        # マド埋まりの●%が達成した場合
                                        if not is_comps[k]:
                                            val = abs(comp_target * after * (comps[1][k] / 100))

                                            if 'up' == updn:
                                                is_comps[k] = low < start - val
                                            else:
                                                is_comps[k] = start + val < high

                                            if is_comps[k]:
                                                vals[height][day + str(comps[1][k])][0] += 1

                                                # print(day + str(comps[1][k]))
                                                # print(comp_target - val)
                                                # print(updn, comp_target)
                                                # print(high)
                                                # print(low)

                            wk_data[str(wk)] = vals
                        mm_data[str(int(mm))] = wk_data
                    datas.append(mm_data)

                # 合計エリアのデータ作成
                month_data = {str(mm): {str(wk): {
                    height: ({**{'half_keep': 0, 'half_out': 0,
                                 'up': 0.0, 'dn': 0.0, 'up_cnt': 0, 'dn_cnt': 0, 'up_rate': 0.0, 'dn_rate': 0.0,
                                 'up_avg': 0.0, 'dn_avg': 0.0, 'rate': 0.0, 'ratio': 0.0, 'pf': 0},
                              **{day + str(comp): [0, {'miss' + str(miss).replace('.', ''): 0 for miss in misses}]
                                 for day in comps[0] for comp in comps[1]}} if float == type(height) else 0)
                    for height in heights} for wk in range(-99, 5) if not -99 < wk < 0} for mm in range(0, 13)}

                # データの集計
                for years in datas:
                    for mm in years:
                        for wk in years[mm]:
                            month_info = ['0', mm]
                            week_info = ['-99', wk]

                            for hh in years[mm][wk]:
                                for mn in month_info:
                                    for wn in week_info:

                                        if float == type(hh):
                                            for keys in years[mm][wk][hh]:

                                                if list == type(years[mm][wk][hh][keys]):
                                                    month_data[mn][wn][hh][keys][0] += years[mm][wk][hh][keys][0]

                                                    for miss in years[mm][wk][hh][keys][1]:
                                                        month_data[mn][wn][hh][keys][1][miss] += years[mm][wk][hh][keys][1][miss]
                                                else:
                                                    month_data[mn][wn][hh][keys] += years[mm][wk][hh][keys]
                                        else:
                                            month_data[mn][wn][hh] += years[mm][wk][hh]

                # 集計データの計算
                trade_info = ['up', 'dn']
                for mm in month_data:
                    for wk in month_data[mm]:
                        month_info = ['0', mm]
                        week_info = ['-99', wk]

                        for hh in month_data[mm][wk]:
                            for mn in month_info:
                                for wn in week_info:

                                    if float == type(hh):

                                        vals = month_data[mn][wn][hh]
                                        month_data[mn][wn][hh]['pf'] = \
                                            ('-' if 0 == vals['dn'] else vals['up'] / -vals['dn'])

                                        count = (vals['up_cnt'] + vals['dn_cnt'])

                                        # マドの出現率(上下合計)
                                        month_data[mn][wn][hh]['rate'] = (0 if 0 == month_data[mn][wn]['total'] else
                                                                          count / month_data[mn][wn]['total'] * 100)

                                        for updn in trade_info:
                                            month_data[mn][wn][hh][updn + '_rate'] = \
                                                (0 if 0 == month_data[mn][wn]['total'] else
                                                 (vals[('up' if 'up' == updn else 'dn') + '_cnt']) /
                                                 month_data[mn][wn]['total'] * 100)

                                            val = (0 if 0 == count else month_data[mn][wn][hh][updn] / count)
                                            month_data[mn][wn][hh][updn + '_avg'] = val

                                        month_data[mn][wn][hh]['ratio'] = ('-' if 0 == vals['dn'] else
                                            month_data[mn][wn][hh]['up_avg'] / -month_data[mn][wn][hh]['dn_avg'])

                # 出力データの文字整形
                for mm in month_data:
                    for wk in month_data[mm]:
                        for hh in list(month_data[mm][wk]):

                            if float == type(hh):

                                if 0 == month_data[mm][wk][hh]['up_cnt'] + month_data[mm][wk][hh]['dn_cnt']:
                                    del month_data[mm][wk][hh]
                                    continue

                                for key in month_data[mm][wk][hh]:
                                    continue
                                    if '-99' == hh and key in ['up', 'dn', 'up_cnt', 'dn_cnt']:
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







                if 0 < len(no_data_msg):
                    com.log(cur + ' データ不足' + no_data_msg)

                jsons.append('"' + cur + '": ' + json.dumps(month_data, ensure_ascii=False, indent=4))
                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + '完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

            with open(PATH + '/content/ShakaiMado.js', 'w') as out:
                out.write('{' + ", ".join([cur_data for cur_data in jsons]) + '}')

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