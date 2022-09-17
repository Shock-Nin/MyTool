#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import json
import glob
import datetime
import pandas as pd
import PySimpleGUI as sg

PATHS = ['H1', 'MTF/H4', 'MTF/D1']
JUDGE_INPUTS = [['期間', 2008, int(com.str_time()[:4]) - 1], ['判定', 10]]
DAYWEEKS = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']


class AnomalyData:

    def __init__(self, function):
        self.function = function

    def do(self):
        getattr(self, '_' + self.function)()

    # ゴトー日とマド空けの実行
    def _specials(self):

        inputs = com.input_box('ゴトー日 & マド空け 開始しますか？', '開始確認', [JUDGE_INPUTS[0]])
        if inputs[0] <= 0:
            return

        err_msg = self._edit_gotobe(inputs)
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        err_msg = self._edit_shakai_mado(inputs)
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        com.dialog('ゴロー日 & マド空け 完了しました。', 'スペシャル作成完了')

    # 通常アノマリ〜のデータ統計
    def _edit_judge(self):

        inputs = com.input_box('アノマリ〜 開始しますか？', '開始確認', JUDGE_INPUTS)
        if inputs[0] <= 0:
            return

        total_time = 0

        mon_cur = {}
        mon_master = {'Month': 0, 'Open': 0.0, 'High': 0.0, 'Low': 9999999.0, 'Close': 0.0}
        mon_names = ['Vola', 'Total', 'UpCnt', 'DnCnt', 'UpVal', 'DnVal']

        value_names = [name for name in [
            'Vola', 'Total', 'WinCnt', 'LoseCnt', 'WinCnt_J', 'LoseCnt_J', 'WinSize', 'LoseSize'
            ] + ['SMA' + no + '_' + updn for no in ['', '3', '4'] for updn in ['Up', 'Dn']]]
        header_names = ['Month', 'Day', 'Hour'] + value_names

        try:
            # 日足から月初と月末10営業日を取得
            files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender/Calc/D1_*.csv'))

            target_days = {files[i].split('/')[- 1].replace('.csv', '').replace('D1_', '') :
                               {} for i in range(0, len(files))}

            for i in range(0, len(files)):
                data = open(files[i], 'r').read().split('\n')
                start_num, end_num = _get_start_end(data, inputs)

                days = []
                ymd = {}
                for k in range(start_num, end_num + 1):
                    rows = data[k].split(',')

                    week_num = datetime.date(int(rows[0]), int(rows[1]), int(rows[2])).weekday() + 1
                    if 5 < week_num:
                        continue

                    days.append([rows[2], float(rows[5])])
                    if int(rows[1]) != int(data[k + 1].split(',')[1]):
                        ymd[rows[0] + rows[1]] = days
                        days = []

                ym = {}
                for key in ymd:
                    starts = []
                    ends = []

                    for k in range(0, len(ymd[key])):
                        starts.append(ymd[key][k])

                        if 10 == len(starts):
                            for m in reversed(range(0, len(ymd[key]))):
                                ends.append(ymd[key][m])

                                if 10 == len(ends):
                                    break
                            break
                    ym[key] = starts + ends
                target_days[files[i].replace('\\', '/').split('/')[- 1].replace('.csv', '').replace('D1_', '')] = ym

                # 月足作成
                mon_datas = []
                day1st = False
                data = open(files[i].replace('Calc', 'MTF'), 'r').read().split('\n')

                start_num = -1
                end_num = -1
                for k in range(0, len(data) - 1):
                    rows = data[k].split(',')[0]

                    if -1 == start_num:
                        if int(rows[: 4]) == int(inputs[1][0]):
                            start_num = k
                    if -1 == end_num:
                        if int(inputs[1][1]) + 1 == int(data[k + 1].split(',')[0][: 4]):
                            end_num = k

                    if int(rows[: 4]) < int(inputs[1][0]):
                        continue
                    elif int(inputs[1][1]) < int(rows[: 4]):
                        break

                for k in range(start_num, end_num):
                    rows = data[k].split(',')

                    if not day1st:
                        day1st = True
                        mon_data = mon_master.copy()
                        mon_data['Month'] = int(rows[0][4:6])
                        mon_data['Open'] = float(rows[2])

                    mon_data['High'] = max(mon_data['High'], float(rows[3]))
                    mon_data['Low'] = min(mon_data['Low'], float(rows[4]))
                    mon_data['Close'] = float(rows[5])

                    if k == end_num - 1 or rows[0][4: 6] != data[k + 1].split(',')[0][4: 6]:
                        day1st = False
                        mon_datas.append(mon_data)

                mon_cur[files[i].replace('\\', '/').split('/')[- 1].replace('.csv', '').replace('D1_', '')] = mon_datas

            # 本データ作成
            for path in PATHS:
                files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender/Calc/') +
                                  path.replace('\\', '/').replace('MTF/', '') + '*.csv')

                cur_name = files[0].replace('\\', '/').split('/')[-1].replace('.csv', '')[3:]
                window = com.progress('判定データ作成中', ['H1', len(PATHS)], [cur_name, len(files)], interrupt=True)
                event, values = window.read(timeout=0)

                window['H1'].update(path.replace('MTF/', ''))
                window['H1_'].update(PATHS.index(path))
                all_targets = {}

                for i in range(0, len(files)):

                    # if files[i].find('D1') < 0:
                    #     continue

                    window[cur_name].update(files[i].split('/')[-1])
                    window[cur_name + '_'].update(i)
                    start_time = com.time_start()

                    data = open(files[i], 'r').read().split('\n')

                    start_num = -1
                    end_num = -1
                    for k in range(0, len(data) - 1):
                        rows = data[k].split(',')

                        if -1 == start_num:
                            if int(rows[0]) == int(inputs[1][0]):
                                start_num = k
                        if -1 == end_num:
                            if int(inputs[1][1]) + 1 == int(data[k + 1].split(',')[0]):
                                end_num = k

                        if int(rows[0]) < int(inputs[1][0]):
                            continue
                        elif int(inputs[1][1]) < int(rows[0]):
                            break

                    # 日と曜日で2巡
                    targets = [[[] for _ in range(0, len(header_names))] for _ in range(0, 2)]
                    dfs = []

                    for k in range(0, len(targets)):

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        count = 0

                        for m in range(start_num, end_num):
                            rows = data[m].split(',')

                            week_num = datetime.date(int(rows[0]), int(rows[1]), int(rows[2])).weekday() + 1
                            if 5 < week_num:
                                continue

                            is_day = False
                            try:
                                days = target_days[cur_name][rows[0] + rows[1]]
                                for day in days:
                                    if day[0] == rows[2]:
                                        count += 1
                                        days = day
                                        is_day = True
                                        break
                            except:
                                continue
                            if not is_day:
                                continue

                            # 月、営業日・曜日、時刻、ボラ、合計用カウント
                            targets[k][0].append(int(rows[1]))

                            day_num = (count if count <= 10 else 10 + (count - 10))
                            count = (0 if 20 == count else count)
                            targets[k][1].append(day_num if 0 == k else str(week_num) + DAYWEEKS[week_num])

                            targets[k][2].append(0 if 'D1' == window['H1'].get() else int(rows[3]))

                            targets[k][3].append(float(rows[5]) / float(rows[4]))
                            targets[k][4].append(1)

                            # 終値上昇回数、終値下落回数、終値上昇回数(判定超え)、終値下落回数(判定超え)、上昇値幅、下落値幅
                            no = 4
                            if float(data[m - 1].split(',')[4]) < float(rows[4]):
                                targets[k][no + 1].append(1)
                                targets[k][no + 2].append(0)
                                targets[k][no + 3].append(0 if 0 == float(rows[5]) else 1
                                if float(inputs[1][2]) < float(days[1]) / float(rows[5]) else 0)
                                targets[k][no + 4].append(0)
                                targets[k][no + 5].append(float(rows[6]) / float(rows[4]))
                                targets[k][no + 6].append(0)

                            elif float(rows[4]) < float(data[m - 1].split(',')[4]):
                                targets[k][no + 1].append(0)
                                targets[k][no + 2].append(1)
                                targets[k][no + 3].append(0)
                                targets[k][no + 4].append(0 if 0 == float(rows[5]) else 1
                                if float(inputs[1][2]) < float(days[1]) / float(rows[5]) else 0)
                                targets[k][no + 5].append(0)
                                targets[k][no + 6].append(float(rows[6]) / float(rows[4]))
                            else:
                                targets[k][no + 1].append(0)
                                targets[k][no + 2].append(0)
                                targets[k][no + 3].append(0)
                                targets[k][no + 4].append(0)
                                targets[k][no + 5].append(0)
                                targets[k][no + 6].append(0)

                            # SMA4本上昇、SMA4本下落、SMA1〜3上昇、SMA1〜3下落、SMA1・2・4上昇、SMA1・2・4下落
                            no = 10
                            if float(data[m - 1].split(',')[9]) < float(rows[9]):

                                up_cnt = (1 if float(data[m - 1].split(',')[7]) < float(rows[7]) else 0)
                                up_cnt += (1 if float(data[m - 1].split(',')[8]) < float(rows[8]) else 0)
                                up_cnt += (1 if float(data[m - 1].split(',')[10]) < float(rows[10]) else 0)

                                targets[k][no + 2].append(0)
                                targets[k][no + 4].append(0)
                                targets[k][no + 6].append(0)
                                if 2 == up_cnt:
                                    targets[k][no + 1].append(0)
                                    targets[k][no + 3].append(1)
                                    targets[k][no + 5].append(0)
                                elif 3 == up_cnt:
                                    targets[k][no + 3].append(1)
                                    targets[k][no + 5].append(1)
                                    if float(data[m - 1].split(',')[10]) < float(data[m - 2].split(',')[10]):
                                        targets[k][no + 1].append(1)
                                    else:
                                        targets[k][no + 1].append(0)
                                else:
                                    targets[k][no + 1].append(0)
                                    targets[k][no + 3].append(0)
                                    targets[k][no + 5].append(0)

                            elif float(rows[9]) < float(data[m - 1].split(',')[9]):

                                dn_cnt = (1 if float(rows[7]) < float(data[m - 1].split(',')[7]) else 0)
                                dn_cnt += (1 if float(rows[8]) < float(data[m - 1].split(',')[8]) else 0)
                                dn_cnt += (1 if float(rows[10]) < float(data[m - 1].split(',')[10]) else 0)

                                targets[k][no + 1].append(0)
                                targets[k][no + 3].append(0)
                                targets[k][no + 5].append(0)
                                if 2 == dn_cnt:
                                    targets[k][no + 2].append(0)
                                    targets[k][no + 4].append(1)
                                    targets[k][no + 6].append(0)
                                elif 3 == dn_cnt:
                                    targets[k][no + 4].append(1)
                                    targets[k][no + 6].append(1)
                                    if float(data[m - 2].split(',')[10]) < float(data[m - 1].split(',')[10]):
                                        targets[k][no + 2].append(1)
                                    else:
                                        targets[k][no + 2].append(0)
                                else:
                                    targets[k][no + 2].append(0)
                                    targets[k][no + 4].append(0)
                                    targets[k][no + 6].append(0)

                            else:
                                targets[k][no + 1].append(0)
                                targets[k][no + 2].append(0)
                                targets[k][no + 3].append(0)
                                targets[k][no + 4].append(0)
                                targets[k][no + 5].append(0)
                                targets[k][no + 6].append(0)

                        dfs.append(pd.DataFrame({header_names[n]: targets[k][n] for n in range(0, len(header_names))}))

                    # 取得データを合算
                    series = {}

                    cur = files[i].replace('\\', '/').split('/')[-1].replace('.csv', '')[3:]
                    is_all = (('USD' == cur[3:] and 'XAUUSD' != cur) or cur[3:] in ['CHF', 'CAD'])

                    for k in range(0, len(dfs)):

                        rows = dfs[k].drop_duplicates(['Month', 'Day', 'Hour'])
                        rows = rows.sort_values(['Month', 'Day', 'Hour'], ascending=[True, True, True])
                        rows = rows.reset_index(drop=True)

                        for m in range(0, len(rows)):

                            mm = rows.at[rows.index[m], 'Month']
                            dd = rows.at[rows.index[m], 'Day']
                            hh = rows.at[rows.index[m], 'Hour']
                            target = dfs[k][(mm == dfs[k]['Month']) & (dd == dfs[k]['Day']) & (hh == dfs[k]['Hour'])]

                            target_count = 0
                            vals = [0.0 for _ in value_names]
                            all_vals = [0.0 for _ in value_names]

                            for key in target:

                                target_count += 1
                                if target_count < 4:
                                    continue

                                vals[target_count - 4] = target[key].sum()
                                if is_all:
                                    all_vals[target_count - 4] = target[key].sum()

                            vals[3 - 3] = float('{:.2f}'.format(vals[3 - 3] / vals[4 - 3] * 100))
                            vals[9 - 3] = (0.0 if 0 == vals[5 - 3] else float('{:.2f}'.format(vals[9 - 3] / vals[5 - 3] * 100)))
                            vals[10 - 3] = (0.0 if 0 == vals[6 - 3] else float('{:.2f}'.format(vals[10 - 3] / vals[6 - 3] * 100)))
                            val_data = {str(value_names[n]): str(vals[n]) for n in range(0, len(vals))}

                            try:
                                series[str(mm)][str(dd)][str(hh)] = val_data
                            except:
                                try:
                                    series[str(mm)][str(dd)]= {str(hh): val_data}
                                except:
                                    series[str(mm)] = {str(dd): {str(hh): val_data}}

                            if is_all:
                                all_vals[3 - 3] += vals[3 - 3]
                                all_vals[9 - 3] += vals[9 - 3]
                                all_vals[10 - 3] += vals[10 - 3]
                                all_val_data = {value_names[n]: str(all_vals[n]) for n in range(0, len(value_names))}

                                try:
                                    all_targets[str(mm)][str(dd)][str(hh)][cur] = all_val_data
                                except:
                                    try:
                                        all_targets[str(mm)][str(dd)][str(hh)] = {cur: all_val_data}
                                    except:
                                        try:
                                            all_targets[str(mm)][str(dd)]= {str(hh): {cur: all_val_data}}
                                        except:
                                            all_targets[str(mm)] = {str(dd): {str(hh): {cur: all_val_data}}}

                    if 0 <= path.find('/D1'):

                        for key in mon_cur:
                            if key != cur:
                                continue

                            for k in range(1, 13):

                                vals = {col: 0.0 for col in mon_names}
                                all_vals = {col: 0.0 for col in mon_names}
                                series[str(k)]['Month'] = {0: []}

                                for m in range(0, len(mon_cur[key])):
                                    data = mon_cur[key][m]

                                    if k != data['Month']:
                                        continue

                                    updn = (1 if data['Open'] < data['Close'] else
                                            -1 if data['Close'] < data[ 'Open'] else 0)

                                    vals['Vola'] += (data['High'] - data['Low']) / data['Close']
                                    vals['Total'] += 1
                                    vals['UpCnt'] += (1 if 0 < updn else 0)
                                    vals['DnCnt'] += (1 if updn < 0 else 0)
                                    vals['UpVal'] += (data['Close'] - data['Open'] if 0 < updn else 0) / data['Close']
                                    vals['DnVal'] += (data['Open'] - data['Close'] if updn < 0 else 0) / data['Close']

                                if is_all:
                                    all_vals['Vola'] += vals['Vola']
                                    all_vals['Total'] += vals['Total']
                                    all_vals['UpCnt'] += vals['UpCnt']
                                    all_vals['DnCnt'] += vals['DnCnt']
                                    all_vals['UpVal'] += vals['UpVal']
                                    all_vals['DnVal'] += vals['DnVal']
                                    all_val_data = {mon_names[n]: str(all_vals[mon_names[n]]) for n in range(0, len(mon_names))}

                                    try:
                                        all_targets[str(k)]['Month'][0][cur] = all_val_data
                                    except:
                                        try:
                                            all_targets[str(k)]['Month'][0] = {cur: all_val_data}
                                        except:
                                            try:
                                                all_targets[str(k)]['Month'] = {0: {cur: all_val_data}}
                                            except:
                                                all_targets[str(k)] = {'Month': {0: {cur: all_val_data}}}

                                series[str(k)]['Month'][0] = {key: (
                                    str(int(vals[key])) if key in ['Total', 'UpCnt', 'DnCnt'] else
                                    str(vals[key])) for key in mon_names}

                    with open(files[i].replace('\\', '/').split('Trender/')[0] + 'Trender/anomaly/judge/' +
                              files[i].replace('\\', '/').split('/')[-1].replace('csv', 'js'), 'w') as out:
                        out.write('const ' + files[i].replace('\\', '/').split('/')[-1].replace('.csv', '') +
                                  ' =\n' + json.dumps(series, ensure_ascii=False, indent=4))

                    run_time = com.time_end(start_time)
                    total_time += run_time
                    com.log(files[i].replace('\\', '/').split('/')[-1] + '判定完了(' + com.conv_time_str(run_time) +
                            ') ' + files[i].replace('\\', '/'))

                master_vals = {col: 0.0 for col in value_names}
                mon_master_vals = {col: 0.0 for col in mon_names}

                for mm in all_targets:
                    for dd in all_targets[mm]:
                        for hh in all_targets[mm][dd]:
                            vals = master_vals.copy()
                            mon_vals = mon_master_vals.copy()

                            for cur in all_targets[mm][dd][hh]:
                                row = all_targets[mm][dd][hh][cur]

                                if 'Month' == dd:
                                    if 'USD' == cur[:3]:
                                        for key in row:
                                            mon_vals[key] += float(row[key])
                                    else:
                                        mon_vals['Vola'] += float(row['Vola'])
                                        mon_vals['Total'] += float(row['Total'])
                                        mon_vals['UpCnt'] += float(row['DnCnt'])
                                        mon_vals['DnCnt'] += float(row['UpCnt'])
                                        mon_vals['UpVal'] += float(row['DnVal'])
                                        mon_vals['DnVal'] += float(row['UpVal'])
                                else:
                                    if 'USD' == cur[:3]:
                                        for key in row:
                                            vals[key] += float(row[key])
                                    else:
                                        vals['Vola'] += float(row['Vola'])
                                        vals['Total'] += float(row['Total'])
                                        vals['WinCnt'] += float(row['LoseCnt'])
                                        vals['LoseCnt'] += float(row['WinCnt'])
                                        vals['WinCnt_J'] += float(row['LoseCnt_J'])
                                        vals['LoseCnt_J'] += float(row['WinCnt_J'])
                                        vals['WinSize'] += (-float(row['LoseSize']))
                                        vals['LoseSize'] += (-float(row['WinSize']))
                                        vals['SMA_Up'] += float(row['SMA_Dn'])
                                        vals['SMA_Dn'] += float(row['SMA_Up'])
                                        vals['SMA3_Up'] += float(row['SMA3_Dn'])
                                        vals['SMA3_Dn'] += float(row['SMA3_Up'])
                                        vals['SMA4_Up'] += float(row['SMA4_Dn'])
                                        vals['SMA4_Dn'] += float(row['SMA4_Up'])

                            if 'Month' == dd:
                                for key in mon_vals:
                                    mon_vals[key] = str(mon_vals[key]) if key in ['Vola', 'UpVal', 'DnVal'] else \
                                        '{:.0f}'.format(mon_vals[key])
                                all_targets[mm][dd][hh] = mon_vals
                            else:
                                for key in vals:
                                    vals[key] = str(vals[key]) if key in ['Vola', 'WinSize', 'LoseSize'] else \
                                        '{:.0f}'.format(vals[key])
                                all_targets[mm][dd][hh] = vals

                with open(files[0].replace('\\', '/').split('Trender/')[0] + 'Trender/anomaly/judge/' +
                          files[0].replace('\\', '/').split('/')[-1][:3] + 'USDIDX.js', 'w') as out:
                    out.write('const ' + files[0].replace('\\', '/').split('/')[-1][:3] +
                              'USDIDX =\n' + json.dumps(all_targets, ensure_ascii=False, indent=4))

                window.close()
        except Exception as e:
            return 'ゴトー日エラー発生: ' + str(e)

        finally:
            try: window.close()
            except: pass

        com.log('判定データ編集完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('判定データ編集完了しました。(' + com.conv_time_str(total_time) + ')', 'MTF作成完了')

        return ''

    # ゴトー日用データ統計
    def _edit_gotobe(self, inputs):

        total_time = 0
        try:
            files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender') + '/H1_??????.csv')

            window = com.progress('ゴトー日データ作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
            event, values = window.read(timeout=0)

            before_days = []
            after_days = []
            start_year = int(inputs[1][0])
            end_year = int(inputs[1][1])

            now_ymd = datetime.date(start_year, 1, 1)
            while now_ymd.year <= end_year:

                now_ymd += datetime.timedelta(days=1)
                if now_ymd.day not in [5, 10, 15, 20, 25, 30, 31]:
                    continue
                if ((now_ymd.month not in [2, 4, 6, 9, 11] and 30 == now_ymd.day)
                        or (now_ymd.month in [2, 4] and 25 < now_ymd.day)
                        or (now_ymd.month in [12] and 20 < now_ymd.day)
                        or (now_ymd.month in [1, 5] and now_ymd.day < 10)):
                    continue

                week_num = now_ymd.weekday() + 1
                str_ymd = now_ymd.strftime('%Y%m%d')

                if 1 == week_num:
                    work_ymd = datetime.date(now_ymd.year, now_ymd.month, now_ymd.day - 3).strftime('%Y%m%d')
                    before_days.append(work_ymd)
                    after_days.append(str_ymd)

                elif week_num in [2, 3, 4, 5]:
                    work_ymd = datetime.date(now_ymd.year, now_ymd.month, now_ymd.day - 1).strftime('%Y%m%d')
                    before_days.append(work_ymd)
                    after_days.append(str_ymd)

                elif 6 == week_num and now_ymd.day in [30, 31]:
                    work_ymd = datetime.date(now_ymd.year, now_ymd.month, now_ymd.day - 2).strftime('%Y%m%d')
                    before_days.append(work_ymd)
                    after_days.append(datetime.date(now_ymd.year, now_ymd.month, now_ymd.day - 1).strftime('%Y%m%d'))

            for i in range(0, len(files)):
                trade_date = {}
                cur = files[i].replace('\\', '/').split('/')[-1].replace('.csv', '')[3:]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                data = open(files[i], 'r').read().split('\n')
                start_num, end_num = _get_start_end(data, inputs)
                before = {'Open': 0.0, 'High': 0.0, 'Low': 9999999.9, 'Close': 0.0,
                          'Trade': -1, 'High_h': -1, 'Low_h': -1, 'Vola': 0.0, 'Before': 0.0}

                for k in range(start_num, end_num + 1):

                    # 中断イベント
                    if _is_interrupt(window, event):
                        return None

                    rows = data[k].split(',')

                    is_before = (rows[0] in before_days)
                    is_after = (rows[0] in after_days and int(rows[1]) <= 5)

                    if not is_before and not is_after:
                        continue

                    for m in range(0, len(before_days)):
                        if rows[0] in [before_days[m], after_days[m]]:
                            before_day = before_days[m]
                            after_day = after_days[m]
                            break

                    date = [after_day[:4], after_day[4:6], after_day[6:]]
                    if is_before:
                        before['Open'] = (float(rows[2]) if 0.0 == before['Open'] else before['Open'])

                        if before['High'] < float(rows[3]):
                            before['High'] = float(rows[3])
                            before['High_h'] = int(rows[1])
                        if float(rows[4]) < before['Low']:
                            before['Low'] = float(rows[4])
                            before['Low_h'] = int(rows[1])

                        before['Close'] = float(rows[5])
                        before['Trade'] = int(before_day)

                    else:
                        if 0 < before['Open']:

                            before['Vola'] = \
                                (float(before['High']) - float(before['Low'])) / float(before['Close'])
                            before['Before'] = \
                                (float(before['Close']) - float(before['Open'])) / float(before['Close'])

                            for key in before:
                                before[key] = ('{:.' + ('0' if key in ['Trade', 'High_h', 'Low_h'] else '5') + 'f}').format(float(before[key]))

                            trade_date[date[0]][date[1]][date[2]]['-1'] = before


                        before = {'Open': 0.0, 'High': 0.0, 'Low': 9999999.9, 'Close': 0.0,
                                  'Trade': -1, 'High_h': -1, 'Low_h': -1, 'Vola': 0.0, 'Before': 0.0}

                    if is_before and int(rows[1]) < 16:
                        continue

                    val = {'Open': float(rows[2]), 'High': float(rows[3]), 'Low': float(rows[4]),
                           'Close': float(rows[5]), 'Trade': int(rows[0])}

                    for key in val:
                        val[key] = ('{:.' + ('0' if key in ['Trade', 'High_h', 'Low_h'] else '5') + 'f}').format(float(val[key]))

                    try:
                        trade_date[date[0]][date[1]][date[2]][rows[1]] = val
                    except:
                        try:
                            trade_date[date[0]][date[1]][date[2]] = {rows[1]: val}
                        except:
                            try:
                                trade_date[date[0]][date[1]] = {date[2]: {rows[1]: val}}
                            except:
                                trade_date[date[0]] = {date[1]: {date[2]: {rows[1]: val}}}

                with open(files[0].replace('\\', '/').split('Trender/')[0] +
                          'Trender/anomaly/special/H1_' + cur + '_GTB.js', 'w') as out:
                    out.write(json.dumps(trade_date, ensure_ascii=False, indent=4))

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + 'ゴトー日完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

        except Exception as e:
            return 'ゴトー日エラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass

        com.log('ゴトー日データ編集完了(' + com.conv_time_str(total_time) + ')')

        return ''

    # マド空け用データ統計
    def _edit_shakai_mado(self, inputs):

        total_time = 0
        try:
            files = glob.glob(
                cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender') + '/H1_??????.csv')

            window = com.progress(
                'マド空けデータ作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
            event, values = window.read(timeout=0)

            fridays = []
            mondays = []
            tuesdays = []
            weeks = []
            count = 0

            start_year = int(inputs[1][0])
            end_year = int(inputs[1][1])

            now_ymd = datetime.date(start_year, 1, 1)
            while now_ymd.year <= end_year:

                now_ymd += datetime.timedelta(days=1)
                if 1 == now_ymd.day:
                    count = 0

                week_num = now_ymd.weekday() + 1
                if week_num not in [1]:
                    continue

                count += 1
                if 5 == count:
                    weeks[-2] = 0
                    weeks[-1] = weeks[-1] - 1
                    count -= 1

                fridays.append((now_ymd - datetime.timedelta(days=3)).strftime('%Y%m%d'))
                mondays.append(now_ymd.strftime('%Y%m%d'))
                tuesdays.append((now_ymd + datetime.timedelta(days=1)).strftime('%Y%m%d'))
                weeks.append(count)

            for i in range(0, len(files)):
                trade_date = {}
                cur = files[i].replace('\\', '/').split('/')[-1].replace('.csv', '')[3:]

                window[files[0].split('/')[-1]].update(cur)
                window[files[0].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                data = open(files[i], 'r').read().split('\n')
                start_num, end_num = _get_start_end(data, inputs)
                before = {'Open': 0.0, 'High': 0.0, 'Low': 9999999.9, 'Close': 0.0,
                          'Real': -1}

                for k in range(start_num, end_num + 1):

                    # 中断イベント
                    if _is_interrupt(window, event):
                        return None

                    rows = data[k].split(',')

                    is_friday = (rows[0] in fridays)
                    is_monday = (rows[0] in mondays)
                    is_tuesday = (rows[0] in tuesdays)

                    if not is_friday and not is_monday and not is_tuesday:
                        continue

                    for m in range(0, len(mondays)):
                        if rows[0] in [fridays[m], mondays[m], tuesdays[m]]:
                            week_no = weeks[m]
                            break

                    hour = (24 if is_tuesday else 0) + int(rows[1])
                    if is_friday:
                        before['Open'] = (float(rows[2]) if 0.0 == before['Open'] else before['Open'])

                        if before['High'] < float(rows[3]):
                            before['High'] = float(rows[3])
                        if float(rows[4]) < before['Low']:
                            before['Low'] = float(rows[4])

                        before['Close'] = float(rows[5])
                        before['Real'] = int(rows[0])

                    else:
                        date = [rows[0][:4], rows[0][4:6], str(week_no)]

                        if is_monday:
                            if 0 < before['Open']:

                                before['Vola'] = \
                                    (float(before['High']) - float(before['Low'])) / float(before['Close'])
                                before['Before'] = \
                                    (float(before['Close']) - float(before['Open'])) / float(before['Close'])
                                before['After'] = \
                                    (float(rows[2]) - float(before['Close'])) / float(before['Close'])

                                for key in before:
                                    before[key] = ('{:.' + ('0' if key in ['Real', 'High_h', 'Low_h'] else '5') +
                                                        'f}').format(float(before[key]))

                                try:
                                    trade_date[date[0]][date[1]][date[2]][hour] = before
                                except:
                                    try:
                                        trade_date[date[0]][date[1]][date[2]] = {-1: before}
                                    except:
                                        try:
                                            trade_date[date[0]][date[1]] = {date[2]: {-1: before}}
                                        except:
                                            trade_date[date[0]] = {date[1]: {date[2]: {-1: before}}}

                        val = {'Open': float(rows[2]), 'High': float(rows[3]), 'Low': float(rows[4]),
                               'Close': float(rows[5]), 'Real': int(rows[0])}

                        for key in val:
                            val[key] = ('{:.' + ('0' if key in ['Real'] else '5') + 'f}').format(float(val[key]))

                        try:
                            trade_date[date[0]][date[1]][date[2]][hour] = val
                        except:
                            try:
                                trade_date[date[0]][date[1]][date[2]] = {hour: val}
                            except:
                                try:
                                    trade_date[date[0]][date[1]] = {date[2]: {hour: val}}
                                except:
                                    trade_date[date[0]] = {date[1]: {date[2]: {hour: val}}}

                        before = {'Open': 0.0, 'High': 0.0, 'Low': 9999999.9, 'Close': 0.0,
                                  'Real': -1}

                with open(files[0].replace('\\', '/').split('Trender/')[0] +
                          'Trender/anomaly/special/H1_' + cur + '_MAD.js', 'w') as out:
                    out.write(json.dumps(trade_date, ensure_ascii=False, indent=4))

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] + 'マド空け完了(' +
                        com.conv_time_str(run_time) + ') ' + files[i].replace('\\', '/'))

        except Exception as e:
            return 'マド空けエラー発生: ' + str(e)
        finally:
            try: window.close()
            except: pass

        com.log('マド空け編集完了(' + com.conv_time_str(total_time) + ')')
        return ''


def _get_start_end(data, inputs):

    start_num = -1
    end_num = -1
    for k in range(0, len(data) - 1):
        rows = data[k].split(',')

        if -1 == start_num:
            if int(rows[0][:4]) == int(inputs[1][0]):
                start_num = k
        if -1 == end_num:
            if int(inputs[1][1]) + 1 == int(data[k + 1].split(',')[0][:4]):
                end_num = k

        if int(rows[0][:4]) < int(inputs[1][0]):
            continue
        elif int(inputs[1][1]) < int(rows[0][:4]):
            break

    return start_num, end_num


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False