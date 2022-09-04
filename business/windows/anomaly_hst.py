#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import json
import glob
import datetime
import pandas as pd

PATHS = ['H1', 'MTF/H4', 'MTF/D1']
MTF_INPUTS = [['SMA', 5, 25, 50, 100]]
JUDGE_INPUTS = [['期間', 2008, int(com.str_time()[:4]) - 1], ['判定', 10]]
DAYWEEKS = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']


class AnomalyHst:

    def __init__(self, function):
        self.function = function

    def do(self):
        if 'create_h1' ==self.function:
            self.create_h1()
        elif 'edit_mtf' ==self.function:
            self.edit_mtf()
        elif 'edit_judge' ==self.function:
            self.edit_judge()

    def create_h1(self):
        if com.question('H1ヒストリカル編集 開始しますか？', '開始確認') <= 0:
            return 0

        files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/') + '/??????.csv')
        total_time = 0

        try:
            for i in range(0, len(files)):
                data = open(files[i], 'r').read().split('\n')

                window = com.progress('H1データ作成中', [files[i].split('/')[-1], len(files)], interrupt=True)
                event, values = window.read(timeout=0)
                window[files[i].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                out = ''
                hi = 0
                lo = 9999999
                count = 0

                for k in range(1, len(data)):
                    rows = data[k].split(',')

                    op = (rows[2] if 0 == count else op)
                    hi = max(float(rows[3]), hi)
                    lo = min(float(rows[4]), lo)
                    count += 1

                    if k == len(data) - 2 or str(data[k + 1].split(',')[1].split(':')[0]) != str(rows[1].split(':')[0]):
                        out += str(rows[0]) + ',' + str(rows[1].split(':')[0]) + ','
                        out += str(op) + ',' + str(hi) + ',' + str(lo) + ',' + rows[5] + '\n'

                        if k == len(data) - 2:
                            break
                        count = 0
                        hi = 0
                        lo = 9999999

                open(files[i].replace('\\', '/').replace('history/', 'Trender/H1_'), 'w').write(out)

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] +
                        '作成完了(' + com.conv_time_str(run_time) + ') ' + files[i])
                window.close()
        finally:
            try: window.close()
            except: pass

        com.log('H1作成完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('H1作成完了しました。(' + com.conv_time_str(total_time) + ')', 'H1作成完了')

        return 0

    def edit_mtf(self):

        inputs = com.input_box('開始しますか？', '開始確認', MTF_INPUTS)
        if inputs[0] <= 0:
            return

        files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender') + '/H1_??????.csv')
        total_time = 0

        window = com.progress(
            'MTFデータ作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
        event, values = window.read(timeout=0)

        try:
            for i in range(0, len(files)):
                data = open(files[i], 'r').read().split('\n')

                window[files[0].split('/')[-1]].update(files[i].split('/')[-1])
                window[files[0].split('/')[-1] + '_'].update(i)

                start_time = com.time_start()

                out_h4 = ''
                hi_h4 = 0
                lo_h4 = 9999999
                count_h4 = 0

                out_d1 = ''
                hi_d1 = 0
                lo_d1 = 9999999
                count_d1 = 0

                for k in range(1, len(data)):
                    rows = data[k].split(',')

                    op_hour_h4 = (rows[1] if 0 == count_h4 else op_hour_h4)
                    op_h4 = (rows[2] if 0 == count_h4 else op_h4)
                    hi_h4 = max(float(rows[3]), hi_h4)
                    lo_h4 = min(float(rows[4]), lo_h4)
                    count_h4 += 1

                    op_hour_d1 = (rows[1] if 0 == count_d1 else op_hour_d1)
                    op_d1 = (rows[2] if 0 == count_d1 else op_d1)
                    hi_d1 = max(float(rows[3]), hi_d1)
                    lo_d1 = min(float(rows[4]), lo_d1)
                    count_d1 += 1

                    if k == len(data) - 2 or 0 == int(data[k + 1].split(',')[1]) % 4:
                        out_h4 += str(rows[0]) + ',' + str(op_hour_h4) + ','
                        out_h4 += str(op_h4) + ',' + str(hi_h4) + ',' + str(lo_h4) + ',' + rows[5] + '\n'
                        if k == len(data) - 2:
                            break
                        count_h4 = 0
                        hi_h4 = 0
                        lo_h4 = 9999999

                    if k == len(data) - 2 or int(rows[0]) != int(data[k + 1].split(',')[0]):
                        out_d1 += str(rows[0]) + ',-,'
                        out_d1 += str(op_d1) + ',' + str(hi_d1) + ',' + str(lo_d1) + ',' + rows[5] + '\n'
                        if k == len(data) - 2:
                            break
                        count_d1 = 0
                        hi_d1 = 0
                        lo_d1 = 9999999

                open(files[i].replace('\\', '/').replace('Trender/H1_', 'Trender/MTF/H4_'), 'w').write(out_h4)
                open(files[i].replace('\\', '/').replace('Trender/H1_', 'Trender/MTF/D1_'), 'w').write(out_d1)

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] +
                        '作成完了(' + com.conv_time_str(run_time) + ') ' + files[i])

            window.close()
        finally:
            try: window.close()
            except: pass

        com.log('MTF作成完了(' + com.conv_time_str(total_time) + ')')
        tf_count = 0

        try:
            for path in PATHS:
                files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender') + '/' + path + '_??????.csv')

                window = com.progress('MTFデータ作成中',
                                      ['H1', len(PATHS)],
                                      [files[0].split('/')[-1], len(files)], interrupt=True)
                event, values = window.read(timeout=0)

                window['H1'].update(path.replace('MTF/', ''))
                window['H1_'].update(tf_count)
                tf_count += 1

                for i in range(0, len(files)):
                    data = open(files[i], 'r').read().split('\n')

                    window[files[0].split('/')[-1]].update(files[i].split('/')[-1])
                    window[files[0].split('/')[-1] + '_'].update(i)
                    start_time = com.time_start()

                    out = ''

                    for k in range(int(inputs[1][len(inputs[1]) - 1]) + 1, len(data) - 1):
                        rows = data[k].split(',')

                        ma_lists = []
                        cl = float(rows[5])

                        for m in range(1, len(MTF_INPUTS[0])):

                            count = 0.0
                            total = 0.0

                            for n in range(0, int(inputs[1][m - 1])):
                                total += float(data[k - n].split(',')[5])
                                count += 1

                            ma_lists.append(total / count)

                        out += rows[0][:4] + ',' + rows[0][4: -2] + ',' + rows[0][-2:] + ',' + str(rows[1]) + ','
                        out += str(cl) + ',' + str(float(rows[3]) - float(rows[4])) + ',' + str(float(rows[5]) - float(rows[2])) + ','
                        out += ",".join(['{:.6f}'.format(ma) for ma in ma_lists]) + '\n'

                    open(files[i].replace('\\', '/').split('Trender/')[0] + 'Trender/Calc/' +
                         files[i].replace('\\', '/').split('/')[-1], 'w').write(out)

                    run_time = com.time_end(start_time)
                    total_time += run_time
                    com.log(files[i].replace('\\', '/').split('/')[-1] +
                            '編集完了(' + com.conv_time_str(run_time) + ') ' + files[i])
                window.close()
        finally:
            try: window.close()
            except: pass

        com.log('データ編集完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('データ編集完了しました。(' + com.conv_time_str(total_time) + ')', 'MTF作成完了')

        return 0

    def edit_judge(self):

        inputs = com.input_box('開始しますか？', '開始確認', JUDGE_INPUTS)
        if inputs[0] <= 0:
            return

        total_time = 0

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
                    data = open(files[i], 'r').read().split('\n')

                    window[cur_name].update(files[i].split('/')[-1])
                    window[cur_name + '_'].update(i)
                    start_time = com.time_start()

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
                    is_all = (('USD' == cur[3:] and 'XAUUSD' != cur) or cur[3:] in ['JPY', 'CHF', 'CAD'])

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
                                all_val_data = {str(value_names[n]): str(all_vals[n]) for n in range(0, len(all_vals))}
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

                    with open(files[i].replace('\\', '/').split('Trender/')[0] + 'Trender/anomaly/judge/' +
                              files[i].replace('\\', '/').split('/')[-1].replace('csv', 'js'), 'w') as out:
                        out.write('const ' + files[i].replace('\\', '/').split('/')[-1].replace('.csv', '') +
                                  ' =\n' + json.dumps(series, ensure_ascii=False, indent=4))

                    run_time = com.time_end(start_time)
                    total_time += run_time
                    com.log(files[i].replace('\\', '/').split('/')[-1] + '判定完了(' + com.conv_time_str(run_time) +
                            ') ' + files[i].replace('\\', '/'))

                master_vals = {col: 0.0 for col in value_names}
                for mm in all_targets:
                    for dd in all_targets[mm]:
                        for hh in all_targets[mm][dd]:
                            vals = master_vals.copy()

                            for cur in all_targets[mm][dd][hh]:
                                row = all_targets[mm][dd][hh][cur]

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

                            for key in vals:
                                vals[key] = str(vals[key]) if key in ['Vola', 'WinSize', 'LoseSize'] else \
                                    '{:.0f}'.format(vals[key])
                            all_targets[mm][dd][hh] = vals

                with open(files[0].replace('\\', '/').split('Trender/')[0] + 'Trender/anomaly/judge/' +
                          files[0].replace('\\', '/').split('/')[-1][:3] + 'USDIDX.js', 'w') as out:
                    out.write('const ' + files[0].replace('\\', '/').split('/')[-1][:3] +
                              'USDIDX =\n' + json.dumps(all_targets, ensure_ascii=False, indent=4))

                window.close()
        finally:
            try: window.close()
            except: pass

        com.log('判定データ編集完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('判定データ編集完了しました。(' + com.conv_time_str(total_time) + ')', 'MTF作成完了')

        return 0
