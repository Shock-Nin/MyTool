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
JPN_DAYWEEKS = ['', '月', '火', '水', '木', '金']


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
        err_msg = self._edit_gotobe()
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

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

        window = com.progress('まとめデータ(ゴトー日)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
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

                            if '1' < wk and '-1' == hh:
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
            return 'まとめデータ(ゴトー日)エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass

        jsons = pd.read_json(PATH + '/content/GoToBe.js').to_dict()
        window = com.progress('コンテンツ(ゴトー日)作成中', ['GoToBe', len(jsons)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0
        cur_msg = {}
        try:
            for cur in jsons:
                mon_msg = {}

                for month in jsons[cur]:
                    wk_msg = {}

                    for week in jsons[cur][month]:

                        if '0' == str(week):
                            continue
                        msg = ''

                        rate = -1
                        pf = -1
                        ratio = -1

                        try:
                            if 1 == int(week):
                                best = jsons[cur][month][week]['-1']
                                pf = float(best['pf'])
                            else:
                                for hour in jsons[cur][month][week]:
                                    if '-99' == hour:
                                        continue

                                    if pf < float(jsons[cur][month][week][hour]['pf']):
                                        best = jsons[cur][month][week][hour]
                                        pf = float(best['pf'])
                                        best_hour = int(hour) + 6 - (24 if 10 < int(hour) else 0)

                        except:
                            com.log(cur + ': ' + str(month) + ', ' + str(week) + ' データ不在')
                            continue

                        msg += '「' + JPN_DAYWEEKS[int(week)] + '曜ゴト〜日」の傾向として、'
                        if 1 < pf:
                            rate = float(best['rate'])
                            ratio = float(best['ratio'])

                            msg += ('オープン直後に' if '1' == str(week) else str(best_hour) + '時頃に')
                            msg += 'ドル買い<br>　→ 9時過ぎ〜10時前決済で、勝率 ' + '{:.2f}'.format(rate) + '%<br>'
                            msg += '[プロフィットファクター ' + '{:.2f}'.format(pf) + ']'
                            msg += '[損益レシオ ' + '{:.2f}'.format(ratio) + ']です。<br>'
                            if 2 < pf:
                                if 65 < rate:
                                    msg += '勝率もPFも非常に高いので、迷いは無用です。'
                                elif 50 < rate:
                                    msg += '勝率が高くPFが非常に高いので、迷いは無用です。'
                                else:
                                    msg += '勝率は低いですがPFは非常に高いので、問題はないでしょう。'
                            elif 1.5 < pf:
                                if 65 < rate:
                                    msg += '勝率もPFも高いので、安心して行きましょう。'
                                elif 50 < rate:
                                    msg += '勝率もPFもそこそこ高いので、継続すれば問題ないでしょう。'
                                else:
                                    msg += '勝率は低いですがPFはそこそこですので、問題はないでしょう。'
                            else:
                                if 65 < rate:
                                    msg += '勝率は高いですがPFがあまり高くないので、雰囲気怪しければ見送りましょう。'
                                elif 50 < rate:
                                    msg += '勝率もPFもあまり高くないので、見送りが無難です。'
                                else:
                                    msg += '勝率もPFも低いので、見送りが無難です。'
                        else:
                            msg += 'ドル買いに適したタイミングはないようです。<br>'
                            msg += '他の通貨でチャンスを探り、次の機会を待ちましょう。'

                        wk_msg[week] = msg + '<br>'
                    mon_msg['total' if '0' == str(month) else str(month)] = wk_msg
                cur_msg[cur] = mon_msg

            with open(PATH + '/content/GoToBe_info.js', 'w') as out:
                out.write('const GOTOBE = ' + json.dumps(cur_msg, ensure_ascii=False, indent=4))

        except Exception as e:
            return 'コンテンツ(ゴトー日)エラー発生: ' + str(e)
        finally:
            try:
                window.close()
            except:
                pass
        return ''

    # マド空けのコンテンツデータ作成
    def _edit_shakai_mado(self):
        files = glob.glob(PATH + '/special/H1_*_MAD.js')

        window = com.progress('まとめデータ(マド空け)作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0

        misses = [0.2, 0.5, 1.0]
        heights = ['total'] + misses
        comps = [['today', 'tomorrow'], [75, 100, 125]]
        try:
            jsons = []
            for i in range(0, len(files)):
                data = pd.read_json(files[i]).to_dict()
                cur = files[i].replace('\\', '/').split('/')[-1].split('_')[1]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                datas = []
                no_data_msg = ''

                # 基本データの計算
                for yy in data:
                    mm_data = {str(mm): {} for mm in range(1, 13)}

                    for mm in data[yy]:
                        wk_data = {str(wk): {} for wk in range(0, 5)}

                        for wk in data[yy][mm]:

                            vals = {height: ({**{'up_cnt': 0, 'dn_cnt': 0, 'half_under': 0},
                                              **{day + str(comp): {
                                                  'miss' + str(miss).replace('.', ''): {
                                                      'win': 0.0, 'win_cnt': 0, 'lose': 0.0, 'lose_cnt': 0
                                                  } for miss in misses } for day in comps[0] for comp in comps[1]}}
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

                                # totalは、何もしない
                                if str == type(height):
                                    continue

                                # オープンから1時間後に、マドの半分以上を埋めた回数
                                val = abs(start * after * 0.5)

                                if 0 < after:
                                    vals[height]['half_under'] += (1 if low < start - val else 0)
                                elif after < 0:
                                    vals[height]['half_under'] += (1 if start + val < high else 0)

                                for k in range(0, len(comps[1])):
                                    for m in range(0, len(misses)):
                                        is_comp = False
                                        is_miss = False

                                        str_miss = 'miss' + str(misses[m]).replace('.', '')

                                        # 高安値で、成否と成功前の失敗をカウント
                                        for hh in data[yy][mm][wk]:

                                            # totalは、何もしない
                                            if -1 == int(hh):
                                                continue

                                            if 24 <= int(hh):
                                                break

                                            high = float(data[yy][mm][wk][hh]['High'])
                                            low = float(data[yy][mm][wk][hh]['Low'])
                                            str_day = 'today' + str(comps[1][k])

                                            # マドがオープンからの逆行が、埋まりより先の場合
                                            if not is_miss and not is_comp:

                                                val = abs(start * misses[m] / 100)
                                                if 'up' == updn:
                                                    is_miss = start + val < high
                                                else:
                                                    is_miss = low < start - val

                                                if is_miss:
                                                    vals[height][str_day][str_miss]['lose_cnt'] += 1
                                                    vals[height][str_day][str_miss]['lose'] += val

                                            # マド埋まりの●%が、逆光より先に達成した場合
                                            if not is_comp and not is_miss:
                                                val = abs(after * (comps[1][k] / 100))

                                                is_comp = (low < start - val
                                                               if 'up' == updn else start + val < high)

                                                if is_comp:
                                                    vals[height][str_day][str_miss]['win_cnt'] += 1
                                                    vals[height][str_day][str_miss]['win'] += val

                                        str_day = 'tomorrow' + str(comps[1][k])
                                        if is_miss:
                                            vals[height][str_day][str_miss]['lose_cnt'] += 1
                                            vals[height][str_day][str_miss]['lose'] += val
                                        if is_comp:
                                            vals[height][str_day][str_miss]['win_cnt'] += 1
                                            vals[height][str_day][str_miss]['win'] += val

                                        for hh in data[yy][mm][wk]:

                                            # totalは、何もしない
                                            if -1 == int(hh):
                                                continue

                                            if int(hh) < 24:
                                                continue

                                            high = float(data[yy][mm][wk][hh]['High'])
                                            low = float(data[yy][mm][wk][hh]['Low'])

                                            # マドがオープンからの逆行が、埋まりより先の場合
                                            if not is_miss and not is_comp:

                                                val = abs(start * misses[m] / 100)
                                                if 'up' == updn:
                                                    is_miss = start + val < high
                                                else:
                                                    is_miss = low < start - val

                                                if is_miss:
                                                    vals[height][str_day][str_miss]['lose_cnt'] += 1
                                                    vals[height][str_day][str_miss]['lose'] += val

                                            # マド埋まりの●%が、逆光より先に達成した場合
                                            if not is_comp and not is_miss:
                                                val = abs(after * (comps[1][k] / 100))

                                                is_comp = (low < start - val
                                                           if 'up' == updn else start + val < high)

                                                if is_comp:
                                                    vals[height][str_day][str_miss]['win_cnt'] += 1
                                                    vals[height][str_day][str_miss]['win'] += val
                            wk_data[str(wk)] = vals
                        mm_data[str(int(mm))] = wk_data
                    datas.append(mm_data)

                # 合計エリアのデータ作成
                month_data = {str(mm): {str(wk): {
                    height: ({**{'up_cnt': 0, 'dn_cnt': 0, 'up_rate': 0.0, 'dn_rate': 0.0,
                                 'half_under': 0, 'half_rate': 0.0},
                              **{day + str(comp): {
                                  'miss' + str(miss).replace('.', ''): {
                                      'win': 0.0, 'win_cnt': 0, 'win_rate': 0.0, 'win_avg': 0.0,
                                      'lose': 0.0, 'lose_cnt': 0, 'lose_rate': 0.0,
                                      'lose_avg': 0.0, 'ratio': 0.0, 'pf': 0} for miss in misses
                              } for day in comps[0] for comp in comps[1]}} if float == type(height) else 0)
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

                                                if type(years[mm][wk][hh][keys]) in [int, float]:
                                                    month_data[mn][wn][hh][keys] += years[mm][wk][hh][keys]
                                                else:
                                                    for miss in years[mm][wk][hh][keys]:
                                                        if type(years[mm][wk][hh][keys]) in [int, float]:
                                                            month_data[mn][wn][hh][keys][miss] += \
                                                                years[mm][wk][hh][keys][miss]
                                                        else:
                                                            for result in years[mm][wk][hh][keys][miss]:
                                                                month_data[mn][wn][hh][keys][miss][result] += \
                                                                    years[mm][wk][hh][keys][miss][result]
                                        else:
                                            month_data[mn][wn][hh] += years[mm][wk][hh]

                # 集計データの計算
                for mm in month_data:
                    for wk in month_data[mm]:
                        month_info = ['0', mm]
                        week_info = ['-99', wk]

                        for hh in month_data[mm][wk]:
                            for mn in month_info:
                                for wn in week_info:

                                    if float != type(hh):
                                        continue

                                    obj = month_data[mn][wn][hh]
                                    total = obj['up_cnt'] + obj['dn_cnt']
                                    if 0 == total:
                                        continue

                                    for keys in obj:

                                        # マドの上下別出現率
                                        if keys.endswith('_cnt'):
                                            updn = keys.split('_')[0]

                                            obj[updn + '_rate'] = \
                                                (0 if 0 == month_data[mn][wn]['total'] else
                                                 (obj[('up' if 'up' == updn else 'dn') + '_cnt']) /
                                                 month_data[mn][wn]['total'] * 100)

                                        # オープン1時間後の、マド残り50%以下確率
                                        elif 'half_under' == keys:
                                            obj['half_rate'] = obj['half_under'] / total * 100

                                        elif keys.startswith('today') or keys.startswith('tomorrow'):

                                            for miss in obj[keys]:

                                                result = obj[keys][miss]
                                                if type(result) in [int, float]:
                                                    continue

                                                result['win_rate'] = result['win_cnt'] / total * 100
                                                result['win_avg'] = (0 if 0 == result['win_cnt'] else
                                                                        result['win'] / result['win_cnt'])

                                                result['lose_rate'] = result['lose_cnt'] / total * 100
                                                result['lose_avg'] = (0 if 0 == result['lose_cnt'] else
                                                                      result['lose'] / result['lose_cnt'])

                                                result['pf'] = (0 if 0 == result['lose'] else
                                                                result['win'] / result['lose'])

                                                result['ratio'] = (0 if 0 == result['lose_avg'] else
                                                                   result['win_avg'] / result['lose_avg'])

                # 出力データの文字整形
                for mm in month_data:
                    for wk in month_data[mm]:

                        for hh in list(month_data[mm][wk]):
                            if float == type(hh):

                                for keys in month_data[mm][wk][hh]:
                                    if type(month_data[mm][wk][hh][keys]) in [float, int]:

                                        month_data[mm][wk][hh][keys] = \
                                            ('{:.' + ('0' if keys.find('rate') < 0 else '3') +
                                             'f}').format(float(month_data[mm][wk][hh][keys]))
                                        month_data[mm][wk][hh][keys] = (
                                            '0' if month_data[mm][wk][hh][keys]
                                        in ['0.000'] else month_data[mm][wk][hh][keys])
                                    else:

                                        for miss in month_data[mm][wk][hh][keys]:
                                            if type(month_data[mm][wk][hh][keys][miss]) in [float, int]:
                                                month_data[mm][wk][hh][keys][miss] = (
                                                    '0' if month_data[mm][wk][hh][keys][miss]
                                                in ['0.000', '0.000000'] else month_data[mm][wk][hh][keys][miss])
                                            else:
                                                for result in month_data[mm][wk][hh][keys][miss]:
                                                    month_data[mm][wk][hh][keys][miss][result] = \
                                                        ('{:.' + ('0' if result.endswith('cnt') else
                                                                  '6' if result.endswith('avg') else '3') +
                                                         'f}').format(float(month_data[mm][wk][hh][keys][miss][result]))
                                                    month_data[mm][wk][hh][keys][miss][result] = (
                                                        '0' if month_data[mm][wk][hh][keys][miss][result]
                                                               in ['0.000', '0.000000'] else
                                                        month_data[mm][wk][hh][keys][miss][result])

                            else:
                                month_data[mm][wk][hh] = \
                                    '{:.0f}'.format(float(month_data[mm][wk][hh]))

                if 0 < len(no_data_msg):
                    com.log(cur + ' データ不足' + no_data_msg)

                jsons.append('"' + cur + '": ' + json.dumps(month_data, ensure_ascii=False, indent=4))
                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + '完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

            with open(PATH + '/content/ShakayMado.js', 'w') as out:
                out.write('{' + ", ".join([cur_data for cur_data in jsons]) + '}')

        # except Exception as e:
        #     return 'まとめデータ(マド空け)エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass

        jsons = pd.read_json(PATH + '/content/ShakayMado.js').to_dict()
        window = com.progress('コンテンツ(マド空け)作成中', ['ShakaiMado', len(jsons)], interrupt=True)
        event, values = window.read(timeout=0)

        total_time = 0
        cur_msg = {}
        try:
            for cur in jsons:
                mon_msg = {}

                for month in jsons[cur]:
                    for week in jsons[cur][month]:

                        if '-99' != week:
                            continue

                        total = float(jsons[cur][month][week]['total'])
                        if 0 == total:
                            continue

                        msg = '<span style="background: #FFFFAA;">'
                        msg += ('全般傾向' if '0' == str(month) else str(month) + '月の傾向') + '</span><br>'
                        height_cnt = 0

                        for height in reversed(jsons[cur][month][week]):
                            if 'total' == height:
                                continue

                            height_cnt += 1
                            height_data = jsons[cur][month][week][height]

                            up_cnt = float(height_data['up_cnt'])
                            dn_cnt = float(height_data['dn_cnt'])
                            up_rate = float(height_data['up_rate'])
                            dn_rate = float(height_data['dn_rate'])
                            mado = up_cnt + dn_cnt

                            msg += '<span style="background: #FFFFCC;">' + str(height_cnt) + '. ' + str(height) + '%以上 アケ率 '
                            msg += '{:.2f}'.format(mado / total * 100) + '%'
                            msg += ' (上' + '{:.2f}'.format(up_rate) + '・下' + '{:.2f}'.format(dn_rate) + ')</span><br>'

                            msg += '　オープン1時間以内の半分以上ウメ率 ' + '{:.2f}'.format(
                                float(height_data['half_rate'])) + '%<br>'
                            msg += '　○ 逆行0.5%未満で100%ウメ達成率 ' + '{:.2f}'.format(
                                float(height_data['today100']['miss05']['win_rate'])) + '%<br>'
                            msg += '　× 逆行0.5%以上の先行率 ' + '{:.2f}'.format(
                                float(height_data['today100']['miss05']['lose_rate'])) + '%<br>'

                            msg += '<details style="padding-left: 20px;"><summary>　詳細分析</summary>'
                            # for miss in height_data[keys][1]:

                            for day_info in [['today', '当日中'], ['tomorrow', '翌日中']]:
                                for keys in height_data:
                                    if type(height_data[keys]) in [float, int] or not keys.startswith(day_info[0]):
                                        continue

                                    for miss in height_data[keys]:
                                        msg += day_info[1] + keys.replace(day_info[0], '')
                                        msg += '%　ウメ' + ('(ブチ抜き)' if keys.endswith('125') else '')
                                        msg += '逆行' + str(int(miss.replace('miss', '')) / 10) + '%<br>'

                                        msg += '　○ [逆行]未満達成率 '
                                        msg += ('' if 0 == mado else '{:.2f}'.format(float(height_data[keys][miss]['win_rate']))) + '% VS '
                                        msg += '　× [逆行]以上先行率 '
                                        msg += ('' if 0 == mado else '{:.2f}'.format(float(height_data[keys][miss]['lose_rate']))) + '%<br>'
                                        msg += '　プロフィットファクタ '
                                        msg += '{:.2f}'.format(float(height_data[keys][miss]['pf'])) + ' : '
                                        msg += '　損益レシオ '
                                        msg += '{:.2f}'.format(float(height_data[keys][miss]['ratio'])) + '<br>'

                            msg += '</details>'
                        mon_msg['total' if '0' == str(month) else str(month)] = msg
                cur_msg[cur] = mon_msg

            with open(PATH + '/content/ShakayMado_info.js', 'w') as out:
                out.write('const SHAKAY_MADO = ' + json.dumps(cur_msg, ensure_ascii=False, indent=4))

        # except Exception as e:
        #     return 'コンテンツ(マド空け)エラー発生: ' + str(e)
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