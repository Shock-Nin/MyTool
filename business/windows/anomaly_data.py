#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from common import my_sql
from const import cst

import glob
import datetime
import statistics
import pandas as pd
import FreeSimpleGUI as sg

PATHS = ['H1', 'MTF/H4', 'MTF/D1']
JUDGE_INPUTS = [['期間', 2008, int(com.str_time()[:4]) - 1]]
DAYWEEKS = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']

SPAN_LIST = ['_D', '_M', '_W']
MODEL_SKIP_DAYS = ['1225', '0101']
USD_IDX = ['EUR', 'GBP', 'AUD', 'CHF', 'CAD']


class AnomalyData:

    def __init__(self, function):
        self.function = function

    def do(self):
        getattr(self, '_' + self.function)()

    # 統計CSV作成
    def _create_stat_csv(self):
        inputs = com.input_box('統計CSV作成 開始しますか？', '開始確認', [
            ['対象年', int(com.str_time()[:4])], ['モデル期間', 15], ['1=H, 2=D, 3=M, 4=W', '1']])
        if inputs[0] <= 0:
            return

        if inputs[1][2] not in ['1', '2', '3', '4']:
            com.dialog('選択が不正です。', '選択不正', lv='W')
            return

        tf = {'1': 'H', '2': 'D', '3': 'M', '4': 'W'}[inputs[1][2]]
        total_time = 0
        start_time = com.time_start()
        try:
            con = my_sql.MySql('fx_history')
            if con.cnx is None:
                com.dialog('DB接続エラーが発生しました。', 'DB接続エラー発生', lv='W')
                return

            year_target = int(inputs[1][0])
            tables = con.free('SHOW TABLES')

            db_datas = {}
            for i in range(len(tables)):

                info = tables[i][0] + ' ' + str(i) + ' / ' + str(len(tables))
                window = com.progress('データ抽出中 ' + tf, [info, len(tables)], interrupt=True)
                event, values = window.read(timeout=0)
                window[info + '_'].update(i)

                db_datas[tables[i][0]] = con.free(
                    'SELECT * FROM ' + tables[i][0]
                    + ' WHERE \'' + str(year_target - int(inputs[1][1]) - 2) + '-01-01\' <= Time'
                    + ' AND Time <= \'' + str(year_target - 1) + '-12-31\'')

                # 中断イベント
                if _is_interrupt(window, event):
                    return

                window.close()

        except Exception as e:
            com.dialog('エラーが発生しました。\n' + str(e), 'データ抽出(' + tf + ')エラー発生', lv='W')
            return

        finally:
            con.close()
            try: window.close()
            except: pass

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('データ抽出(' + tf + ')完了(' + com.conv_time_str(total_time) + ')')

        if inputs[1][2] in ['2', '3', '4']:
            try:
                start_time = com.time_start()
                cnt = 0
                len_date = (10 if inputs[1][2] in ['2', '4'] else 7)

                for table in db_datas:

                    window = com.progress('H1時間足変換中 ' + tf, [table, len(db_datas[table])], interrupt=True)
                    event, values = window.read(timeout=0)
                    window[table + '_'].update(cnt)

                    start_time = com.time_start()
                    old_date = '1999-01-01'
                    rates = []

                    for i in range(len(db_datas[table])):

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return

                        data = db_datas[table][i]
                        if str(data[0])[:len_date] == str(old_date)[:len_date]:
                            continue

                        old_date = data[0]
                        op = data[1]
                        hi = data[2]
                        lo = data[3]

                        for k in range(i + 1, len(db_datas[table])):
                            rows = db_datas[table][k]

                            if str(rows[0])[:len_date] != str(old_date)[:len_date]:
                                break

                            if '3' == inputs[1][2]:
                                if str(old_date)[5:7] != str(rows[0])[5:7]:
                                    break

                            hi = max(rows[2], hi)
                            lo = min(rows[3], lo)
                            cl = rows[4]

                        rates.append([datetime.datetime(
                            int(str(old_date)[:4]), int(str(old_date)[5:7]),
                            (int(str(old_date)[8:10])) if inputs[1][2] in ['2', '4'] else 1), op, hi, lo, cl])

                    db_datas[table] = rates
                    cnt += 1
                    window.close()

            except Exception as e:
                com.dialog('エラーが発生しました。\n' + str(e), '時間足変換(' + tf + ')エラー発生', lv='W')
                return
            finally:
                try: window.close()
                except: pass

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log('H1時間足変換(' + tf + ')完了(' + com.conv_time_str(total_time) + ')')

        try:
            times = []
            for table in db_datas:
                for i in range(len(db_datas[table])):
                    times.append(db_datas[table][i][0])
            times = sorted(list(set(times)))

            target_times = []
            for year in range((int(inputs[1][0]) - int(inputs[1][1]) - 2), int(com.str_time()[:4])):
                for i in range(len(times)):
                    if int(times[i].strftime('%Y')) == year:

                        if inputs[1][2] in ['3'] or times[i].strftime('%m%d') not in MODEL_SKIP_DAYS:
                            target_times.append(times[i])
            cnt = 0
            for year in range((int(inputs[1][0]) - int(inputs[1][1]) - 2), int(com.str_time()[:4])):

                start_time = com.time_start()
                window = com.progress('データ編集中 ' + tf, [str(year), len(target_times)], interrupt=True)
                event, values = window.read(timeout=0)

                str_out = ''
                old = {table: -1 for table in db_datas}

                for i in range(cnt, len(target_times)):
                    window[str(year)+ '_'].update(i)
                    data = ''

                    if year < int(target_times[i].strftime('%Y')):
                        break

                    for table in db_datas:
                        is_time = False

                        for k in range(len(db_datas[table])):

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return

                            row = db_datas[table][k]

                            if year < int(row[0].strftime('%Y')) or target_times[i] < row[0]:
                                break

                            elif target_times[i] == row[0]:
                                op = (row[1] if -1 == old[table] else old[table])
                                data += str(row[4]) + ',' + '{:.6f}'.format(row[2] - row[3]) + ',' \
                                    + '{:.6f}'.format(op - row[4] if table.startswith('usd') else row[4] - op) + ','

                                old[table] = row[4]
                                is_time = True

                                del db_datas[table][k]
                                break

                        if not is_time:
                            data += (',,,' if -1 == old[table] else str(old[table]) + ',0,0,')

                    str_out += target_times[i].strftime('%Y-%m'
                        + ('|' + DAYWEEKS[target_times[i].weekday() + 1] if inputs[1][2] in ['4'] else '' if inputs[1][2] in ['3'] else '-%d')
                        + (' %H:%M:%S' if '1' == inputs[1][2] else '')) + ',' + data[:-1] + '\n'
                    cnt += 1

                with open(cst.HST_PATH[cst.PC].replace('\\', '/') + '_stat/' + str(year)
                                + {'1': 'H', '2': 'D', '3': 'M', '4': 'W'}[inputs[1][2]] + '.csv', 'w') as out:
                    out.write('Time,' + ','.join(''.join(
                        table.upper() + col for col in [',', '_Vola,', '_UpDn']) for table in db_datas) + '\n' + str_out)

                window.close()
                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(str(year) + '年(' + tf + ')書き出し完了(' + com.conv_time_str(total_time) + ')')

        except Exception as e:
            com.dialog('エラーが発生しました。\n' + str(e), 'データ編集(' + tf + ')エラー発生', lv='W')
            return
        finally:
            try: window.close()
            except: pass

        com.log('統計CSV作成(' + tf + ')完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('統計CSV作成(' + tf + ')完了しました。(' + com.conv_time_str(total_time) + ')', '統計CSV作成完了')

        return ''

    # 予測編集
    def _edit_normal(self, inputs, dfs):

        start_time = com.time_start()
        total_time = 0

        year_target = int(inputs[1][0])
        forecasts = [[] for _ in dfs]

        for i in range(len(forecasts)):
            date = datetime.datetime(year_target - 1 + i, 1, 1)

            while date.year == year_target - 1 + i:

                if ('0' if date.month < 10 else '') + str(date.month) + ('0' if date.day < 10 else '') + str(date.day) \
                        not in MODEL_SKIP_DAYS and date.weekday() < 5:
                    forecasts[i].append(date)

                date += datetime.timedelta(days=1)

        out_path = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'anomaly/')
        cols = ''
        curs = []

        for col in dfs[0][0].keys():
            if col in ['Time'] or 0 <= col.find('_Vola') or 0 <= col.find('_UpDn'):
                continue

            curs.append(col)
            cur_col = col + ',' + col + '_VolaAvg,' + col + '_VolaMax,' + col + '_VolaMin,' + col + '_UpDnAvg,'
            cur_col += col + '_Win,' + col + '_Lose,' + col + '_WinPc,' + col + '_LosePc,'
            cur_col += col + '_WinAvg,' + col + '_LoseAvg,'

            if 0 == len(cols):
                cols = cur_col.replace(col, 'USD')
            cols += cur_col.replace('USD', '')

        try:
            for i in range(len(dfs)):

                data_d = dfs[i][1]
                data_m = dfs[i][2]
                data_w = dfs[i][3]

                str_out = ''

                for time in forecasts[i]:
                    row_d = data_d[data_d['Time'].str.match('20..-' + time.strftime('%m-%d'))].copy()
                    row_m = data_m[data_m['Time'].str.match('20..-' + time.strftime('%m'))].copy()
                    row_w = data_w[data_w['Time'].str.match('20..-' + time.strftime('%m') + '.' + DAYWEEKS[time.weekday() + 1])].copy()

                    row_d = row_d.reset_index(drop=True)
                    row_m = row_m.reset_index(drop=True)
                    row_w = row_w.reset_index(drop=True)
                    rows = [row_d, row_m, row_w]

                    str_out += str(time)

                    for row in rows:
                        str_updn = ''
                        indexes = ['', 0, 0, 0, 9999999999, 0, 0, 0, 0, 0, 0]

                        for cur in curs:

                            count = len(row)

                            vola = 0
                            vola_max = 0
                            vola_min = 9999999999
                            updn = 0
                            count_win = 0
                            count_lose = 0
                            updn_win = 0
                            updn_lose = 0

                            for k in range(len(row)):

                                get_vola = row.at[row.index[k], cur + '_Vola'] / row.at[row.index[k], cur] * 100
                                get_updn = row.at[row.index[k], cur + '_UpDn'] / row.at[row.index[k], cur] * 100
                                if 'nan' == str(get_updn) or 'nan' == str(get_vola):
                                    continue

                                vola += get_vola
                                vola_max = max(vola_max, get_vola)
                                vola_min = min(vola_min, get_vola)

                                updn += get_updn

                                if get_updn < 0:
                                    count_lose += 1
                                    updn_lose += get_updn
                                if 0 < get_updn:
                                    count_win += 1
                                    updn_win += get_updn

                            str_updn += ',' + str(count) + ',' + '{:.2f}'.format(vola / count) + ','
                            str_updn += '{:.2f}'.format(vola_max) + ',' + '{:.2f}'.format(vola_min) + ','

                            str_updn += '{:.2f}'.format(updn / count) + ',' + str(count_win) + ',' + str(count_lose) + ','
                            str_updn += '{:.2f}'.format(count_win / count * 100) + ','
                            str_updn += '{:.2f}'.format(count_lose / count * 100) + ','
                            str_updn += '{:.2f}'.format(0 if 0 == count_win else updn_win / count_win) + ','
                            str_updn += '{:.2f}'.format(0 if 0 == count_lose else updn_lose / count_lose)

                            if cur.replace('USD', '') in USD_IDX:
                                indexes[1] += count
                                indexes[2] += vola
                                indexes[3] = max(vola_max, indexes[3])
                                indexes[4] = min(vola_min, indexes[4])
                                indexes[5] += updn
                                indexes[6] += count_win
                                indexes[7] += count_lose
                                indexes[8] += updn_win
                                indexes[9] += updn_lose

                        str_updn_idx = ',' + str(indexes[1]) + ',' + '{:.2f}'.format(indexes[2] / indexes[1]) + ','
                        str_updn_idx += '{:.2f}'.format(indexes[3]) + ',' + '{:.2f}'.format(indexes[4]) + ','

                        str_updn_idx += '{:.2f}'.format(indexes[5] / indexes[1]) + ',' + str(indexes[6]) + ',' + str(indexes[7]) + ','
                        str_updn_idx += '{:.2f}'.format(indexes[6] / indexes[1] * 100) + ','
                        str_updn_idx += '{:.2f}'.format(indexes[7] / indexes[1] * 100) + ','
                        str_updn_idx += '{:.2f}'.format(0 if 0 == indexes[6] else indexes[8] / indexes[6]) + ','
                        str_updn_idx += '{:.2f}'.format(0 if 0 == indexes[7] else indexes[9] / indexes[7])

                        str_out += str_updn_idx + str_updn
                    str_out += '\n'

                with open(out_path + 'Year' + ['1', '2', '3'][i] + '.csv', 'w') as out:
                    out.write('Time,' + ''.join(cols.replace(',', span + ',')
                                                for span in SPAN_LIST)[:-1] + '\n' + str_out)

            run_time = com.time_end(start_time)
            total_time += run_time

        except Exception as e:
            return '予測データ編集でエラーが発生しました。\n' + str(e)

        com.log('予測データ編集完了(' + com.conv_time_str(total_time) + ')')
        return ''

    # ゴトー日編集
    def _edit_gotobe(self, inputs, dfs, h_data):

        start_time = com.time_start()
        total_time = 0

        year_target = int(inputs[1][0])
        forecasts = [[] for _ in dfs]

        for i in range(len(forecasts)):
            date = datetime.datetime(year_target - 1 + i, 1, 1)

            while date.year == year_target - 1 + i:

                if ('0' if date.month < 10 else '') + str(date.month) + ('0' if date.day < 10 else '') + str(date.day) \
                        not in MODEL_SKIP_DAYS and date.weekday() < 5:

                    is_ok = date.day in [10, 15, 20]
                    if not is_ok:
                        if date.month in [6, 9, 11] and 30 == date.day:
                            is_ok = True
                        elif date.month not in [12] and date.day in [25, 31]:
                            is_ok = True
                        elif date.month not in [1, 5] and 5 == date.day:
                            is_ok = True

                    if is_ok:
                        forecasts[i].append([date.weekday(), date])

                date += datetime.timedelta(days=1)
        cols = ''
        curs = []
        str_outs = []
        start_hours = 5
        close_hours = [2, 3, 4]
        gets = [0, 1, 2]
        spans = ['Total'] + [('0' if i < 10 else '') + str(i) + span \
                             for i in range(1, 13) for span in ['D5', 'D0', 'Mst', 'Med']] \
                + [DAYWEEKS[i] for i in range(1, len(DAYWEEKS))]

        for col in dfs[0][0].keys():
            if col in ['Time'] or 0 <= col.find('_Vola') or 0 <= col.find('_UpDn') or col.startswith('Z_'):
                continue

            curs.append(col)
            col = col.replace('USD', '')
            cols += ',' + col + ',' + col + '_BestOpenMon,' + col + '_BestCloseMon,' + col + '_BestOpen,' + col + '_BestClose' \
                    + ''.join(',' + col + '_Win' + str(w) + 'H' + str(h) + ','
                              + col + '_Win' + str(w) + 'H' + str(h) + 'Pc' for h in close_hours for w in gets) \
                    + ''.join(',' + col + '_LoseH' + str(h) + ','
                              + col + '_LoseH' + str(h) + 'Pc' for h in close_hours)
        try:
            for i in range(len(dfs)):
                counts = [{s: [0, [], [], [], [],
                               [0 for _ in close_hours for _ in gets],
                               [0 for _ in close_hours]] for s in spans} for _ in curs]

                for k in range(len(forecasts[i])):

                    info = str(forecasts[i][k][1])[:7] + ' (' + str(k) + ' / ' + str(len(forecasts[i])) + ')'
                    window = com.progress('ゴト〜日編集中', [info, len(forecasts[i])], interrupt=True)
                    event, values = window.read(timeout=0)
                    window[info + '_'].update(k)

                    for c in range(len(curs)):
                        cur = curs[c].lower()

                        gotobe = []
                        old_date = ''
                        for g in range(len(h_data[curs[c].lower()])):
                            if 4 < h_data[cur][g][0].weekday():
                                continue

                            if old_date == str(h_data[cur][g][0])[:10]:
                                gotobe[len(gotobe) - 1][1].append(h_data[cur][g])
                            else:
                                old_date = h_data[cur][g][0]
                                gotobe.append([old_date, [h_data[cur][g]]])
                                old_date = str(old_date)[:10]

                        for m in range(len(gotobe)):

                            day_close = gotobe[m][0]
                            if (year_target - (2 if len(dfs) - 1 == i else 1) + i) == day_close.year \
                                    or day_close.year < (year_target - int(inputs[1][1]) - (3 if len(dfs) - 1 == i else 2) + i) \
                                    or day_close.strftime('%m-%d') != forecasts[i][k][1].strftime('%m-%d'):
                                continue

                            day_open = gotobe[m][0]
                            if 0 < day_open.weekday():
                                day_open -= datetime.timedelta(days=1)

                            summer_time = (1 if 2 < day_close.month < 11 else 0)

                            open_h = []
                            close_h = []
                            for g in range(len(gotobe)):
                                if day_close.strftime('%Y-%m-%d') != gotobe[g][0].strftime('%Y-%m-%d') \
                                        or day_close.strftime('%m-%d') != forecasts[i][k][1].strftime('%m-%d'):
                                    continue

                                if 0 == day_close.weekday():
                                    for h in range(len(gotobe[m][1])):
                                        if gotobe[m][1][h][0].hour < 2:
                                            open_h.append(gotobe[m][1][h])
                                        elif gotobe[m][1][h][0].hour in close_hours:
                                            close_h.append(gotobe[m][1][h])
                                else:
                                    for h in range(len(gotobe[g][1])):
                                        if 18 < gotobe[g][1][h][0].hour:
                                            open_h.append(gotobe[g][1][h])
                                break

                            if 0 < day_close.weekday():
                                for g in range(len(gotobe)):
                                    if day_close.strftime('%Y-%m-%d') != gotobe[g][0].strftime('%Y-%m-%d') \
                                            or day_close.strftime('%m-%d') != forecasts[i][k][1].strftime('%m-%d'):
                                        continue

                                    for h in range(len(gotobe[g][1])):
                                        if gotobe[g][1][h][0].hour < 2:
                                            open_h.append(gotobe[g][1][h])
                                        elif gotobe[g][1][h][0].hour in close_hours:
                                            close_h.append(gotobe[g][1][h])
                                    break

                            if 0 == len(open_h) or 0 == len(close_h):

                                msg = cur + ', ' + str(forecasts[i][k][1]) + ' | ' + str(day_close.weekday()) + ', '
                                msg += str(day_open) + ' ' + ('×' if 0 == len(open_h)else '○') + ', '
                                msg += str(day_close) + ' ' + ('×' if 0 == len(close_h) else '○')

                                #TODO
                                # print(msg)
                                continue

                            str_month = ('0' if day_close.month < 10 else '') + str(day_close.month)
                            types = [
                                'Total',
                                str_month + ('D5' if str(day_close.day).endswith('5') else 'D0'),
                                str_month + ('Mst' if day_close.day < 16 else 'Med'),
                                DAYWEEKS[day_close.weekday() + 1]
                            ]

                            hi = 0
                            lo = 9999999999
                            hi_h = -999
                            lo_h = -999
                            for h in range(len(open_h)):
                                if hi < open_h[h][2]:
                                    hi = open_h[h][2]
                                    hi_h = h
                                if open_h[h][3] < lo:
                                    lo = open_h[h][3]
                                    lo_h = h

                            hl = (lo_h if curs[c].startswith('USD') else hi_h)
                            for t in types:
                                counts[c][t][0] += 1
                                counts[c][t][1 if 0 == open_h[hl][0].weekday() else 3].append(
                                    0 if 24 == open_h[hl][0].hour + summer_time else open_h[hl][0].hour + summer_time)
                            open_price = open_h[hl][1]

                            hi = 0
                            lo = 9999999999
                            hi_h = -999
                            lo_h = -999
                            cnt = 0
                            for h in range(len(close_h)):
                                if hi < close_h[h][2]:
                                    hi = close_h[h][2]
                                    hi_h = h
                                if close_h[h][3] < lo:
                                    lo = close_h[h][3]
                                    lo_h = h

                                for g in gets:
                                    if curs[c].startswith('USD'):
                                        is_win = open_price + (open_price * (g / 1000)) < close_h[h][4]
                                    else:
                                        is_win = close_h[h][4] < open_price - (open_price * (g / 1000))
                                    if is_win:
                                        for t in types:
                                            counts[c][t][start_hours][cnt] += 1
                                    cnt += 1

                                if curs[c].startswith('USD'):
                                    is_lose = close_h[h][4] <= open_price
                                else:
                                    is_lose = open_price <= close_h[h][4]
                                if is_lose:
                                    for t in types:
                                        counts[c][t][start_hours + 1][h] += 1

                            hl = (hi_h if curs[c].startswith('USD') else lo_h)
                            for t in types:
                                counts[c][t][2 if 0 == close_h[hl][0].weekday() else 4].append(
                                    0 if 24 == close_h[hl][0].hour + summer_time else close_h[hl][0].hour + summer_time)

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return None
                    window.close()

                str_curs = []
                for c in range(len(curs)):
                    str_cur = {}

                    for str_span in counts[c]:
                        str_time = str(year_target - 1 + i) + '|' + str_span
                        count = counts[c][str_span][0]

                        str_cur[str_time] = ',' + str(count)
                        if 0 == count:
                            str_cur[str_time] += ',,,,'
                        else:
                            str_cur[str_time] += ''.join(',' + (
                                '' if 0 == len(counts[c][str_span][k]) else
                                str(statistics.mode(counts[c][str_span][k]))) for k in range(1, 5))

                        cnt = 0
                        for h in range(len(close_hours)):
                            for g in range(len(gets)):
                                if 0 == count:
                                    str_cur[str_time] += ',,'
                                else:
                                    str_cur[str_time] += ',' + str(counts[c][str_span][start_hours][cnt])
                                    str_cur[str_time] += ',' + ('0' if 0 == counts[c][str_span][start_hours][cnt] else
                                                                '{:.2f}'.format(counts[c][str_span][start_hours][cnt] / count * 100))
                                cnt += 1
                        for h in range(len(close_hours)):
                            if 0 == count:
                                str_cur[str_time] += ',,'
                            else:
                                str_cur[str_time] += ',' + str(counts[c][str_span][start_hours + 1][h])
                                str_cur[str_time] += ',' + ('0' if 0 == counts[c][str_span][start_hours + 1][h] else
                                                            '{:.2f}'.format(counts[c][str_span][start_hours + 1][h] / count * 100))

                    str_curs.append(str_cur)
                times = []
                datas = []
                for cur in str_curs:
                    for str_time in cur:
                        if str_time not in times:
                            times.append(str_time)
                        datas.append(cur[str_time] + '\n')

                str_rows = []
                str_row = ''
                cnt = 0

                for cur in datas:
                    str_row += cur
                    cnt += 1

                    if cnt == len(times):
                        str_rows.append(str_row)
                        str_row = ''
                        cnt = 0

                for t in range(len(times)):
                    row = ''

                    for cur in str_rows:
                        row += cur.split('\n')[t]

                    str_outs.append(times[t] + row)

                run_time = com.time_end(start_time)
                total_time += run_time

                com.log(str(year_target - 1 + i) + ' 作成完了(' + com.conv_time_str(total_time) + ')')

            out_path = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'anomaly/')

            with open(out_path + 'GoToBe' + '.csv', 'w') as out:
                out.write('Time' + cols + ''.join('\n' + out for out in str_outs).replace('|Total', ''))

        except Exception as e:
            return 'ゴト〜日編集でエラーが発生しました。\n' + str(e)
        finally:
            try: window.close()
            except: pass

        com.log('ゴト〜日編集完了(' + com.conv_time_str(total_time) + ')')
        return ''

    # マド空け編集
    def _edit_shakay_mado(self, inputs, dfs, h_window):

        start_time = com.time_start()
        total_time = 0

        year_target = int(inputs[1][0])
        forecasts = [[] for _ in dfs]

        for i in range(len(forecasts)):
            date = datetime.datetime(year_target - 1 + i, 1, 1)

            while date.year == year_target - 1 + i:
                if 1 == date.day:
                    forecasts[i].append(date)
                date += datetime.timedelta(days=1)

        cols = ''
        curs = []
        str_years = [[] for _ in dfs]
        heights = [2, 3, 5]
        achieves = [75, 100, 125]
        attainments = ['W', 'L', 'N']
        updns = ['Up', 'Dn', '']

        for col in dfs[0][0].keys():
            if col in ['Time'] or 0 <= col.find('_Vola') or 0 <= col.find('_UpDn'):
                continue

            curs.append(col)
            col = col.replace('USD', '')
            cols += col + ',' + ''.join(
                [col + '_' + '0' + str(height) + ',' + col + '_' + '0' + str(height) + 'Pc,' + ''.join(
                    [col + '_' + '0' + str(height) + win_lose + str(achieve) + ','
                     + col + '_' + '0' + str(height) + win_lose + str(achieve) + 'Pc,'
                     for achieve in achieves for win_lose in attainments]) for height in heights])
        try:
            for i in range(len(dfs)):

                data_d = dfs[i][1]
                totals = [[0,
                          {height: 0 for height in heights},
                          {height: 0 for height in heights},
                          [[[0 for _ in achieves] for _ in attainments] for _ in heights],
                          [[[0 for _ in achieves] for _ in attainments] for _ in heights]
                          ] for _ in curs]

                for k in range(len(forecasts[i])):

                    info = str(forecasts[i][k])[:7] + ' (' + str(k) + ' / ' + str(len(forecasts[i])) + ')'
                    window = com.progress('マド空け編集中', [info, len(forecasts[i])], interrupt=True)
                    event, values = window.read(timeout=0)
                    window[info + '_'].update(k)

                    str_updns = ['', '', '']

                    for c in range(len(curs)):
                        cur = curs[c].lower()

                        counts = [0,
                                  {height: 0 for height in heights},
                                  {height: 0 for height in heights},
                                  [[[0 for _ in achieves] for _ in attainments] for _ in heights],
                                  [[[0 for _ in achieves] for _ in attainments] for _ in heights]
                                  ]
                        windows = [[], []]
                        mondays = []
                        old_day = 0

                        for w in range(len(h_window[curs[c].lower()])):
                            num = h_window[cur][w][0].weekday()
                            windows[num].append(h_window[cur][w])

                            if 0 == num:
                                if old_day != h_window[cur][w][0].day:
                                    mondays.append(h_window[cur][w])
                                    old_day = h_window[cur][w][0].day

                        for m in range(len(mondays)):

                            time_monday = mondays[m][0]
                            if forecasts[i][k].strftime('-%m-%d') != time_monday.strftime('-%m-01') \
                                    or (year_target - (2 if len(dfs) - 1 == i else 1) + i) == time_monday.year \
                                    or time_monday.year < (year_target - int(inputs[1][1]) - (3 if len(dfs) - 1 == i else 2) + i) \
                                    or (12 == time_monday.month and 22 < time_monday.day) \
                                    or (1 == time_monday.month and time_monday.day < 6):
                                continue

                            fridays = data_d[data_d['Time'].str[:10] ==
                                (time_monday - datetime.timedelta(days=3)).strftime('%Y-%m-%d')].copy()
                            fridays = fridays.reset_index(drop=True)


                            if 0 == len(fridays) or 'nan' == str(fridays.at[fridays.index[0], curs[c]]):

                                msg = cur + ', ' + str(forecasts[i][k]) + ' | '
                                msg += (time_monday - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
                                msg += ' ' + ('×' if 0 == len(fridays) or 'nan' == str(fridays.at[fridays.index[0], curs[c]]) else '○')
                                msg += ', ' + str(time_monday)

                                # TODO
                                # print(msg)
                                continue

                            counts[0] += 1
                            totals[c][0] += 1

                            hours = []
                            op = mondays[m][1]

                            for hour in windows[0]:
                                if str(hour[0])[:10] == str(mondays[m][0])[:10]:
                                    hours.append(hour)
                                    if 23 == hour[0].hour:
                                        break

                            cl = fridays.at[fridays.index[0], curs[c]]
                            updn = (cl - op if curs[c].startswith('USD') else op - cl)
                            updn = round(updn, 6)

                            for height in range(len(heights)):
                                if round(abs(updn) / op * 1000, 2) < heights[height]:
                                    continue

                                num = (2 if updn < 0 else 1)
                                counts[num][heights[height]] += 1
                                totals[c][num][heights[height]] += 1

                                for a in range(len(achieves)):
                                    achieve_rate = round(abs(updn) * (achieves[a] / 100), 6)

                                    win = 0
                                    lose = 0

                                    for hour in hours:

                                        is_high = op + achieve_rate <= hour[2]
                                        is_low = hour[3] <= op - achieve_rate

                                        if updn < 0:
                                            if is_high:
                                                if curs[c].startswith('USD'):
                                                    lose = 1
                                                else:
                                                    win = 1
                                            if is_low:
                                                if curs[c].startswith('USD'):
                                                    win = 1
                                                else:
                                                    lose = 1
                                        else:
                                            if is_high:
                                                if curs[c].startswith('USD'):
                                                    win = 1
                                                else:
                                                    lose = 1
                                            if is_low:
                                                if curs[c].startswith('USD'):
                                                    lose = 1
                                                else:
                                                    win = 1

                                        if 0 < win + lose:
                                            break
                                    #
                                    # if 0 < win + lose:
                                    #     print(str(hour[0])[:16], cur, ('-' if updn < 0 else '+'), cl, op, ' | ',
                                    #           achieves[a], achieve_rate, win, lose, ' | ',
                                    #           op + achieve_rate <= hour[2], round(op + achieve_rate, 6), hour[2], ' | ',
                                    #           hour[3] <= op - achieve_rate, round(op - achieve_rate, 6), hour[3])

                                    neither = 0
                                    if 1 != win + lose:
                                        win = 0
                                        lose = 0
                                        neither = 1

                                    counts[num + 2][height][0][a] += win
                                    totals[c][num + 2][height][0][a] += win
                                    counts[num + 2][height][1][a] += lose
                                    totals[c][num + 2][height][1][a] += lose
                                    counts[num + 2][height][2][a] += neither
                                    totals[c][num + 2][height][2][a] += neither

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return None

                        opens = []
                        closes = []

                        for cnt_updn in range(len(str_updns) - 1):
                            cnt1 = cnt_updn + 1
                            cnt3 = cnt_updn + 3

                            str_updns[cnt_updn] += ','
                            if len(str_updns) - 2 == cnt_updn:
                                str_updns[len(str_updns) - 1] += ','+ str(counts[0])

                            opens.append(counts[cnt1])
                            closes.append(counts[cnt3])

                            for height in range(len(heights)):

                                str_updns[cnt_updn] += ',' + str(opens[cnt_updn][heights[height]]) + ',' +'{:.2f}'.format(opens[cnt_updn][heights[height]] / counts[0] * 100)
                                if len(str_updns) - 2 == cnt_updn:
                                    str_updns[len(str_updns) - 1] += \
                                        ',' + str(opens[0][heights[height]] + opens[1][heights[height]]) + ',' \
                                        + '{:.2f}'.format((opens[0][heights[height]] + opens[1][heights[height]]) / counts[0] * 100)

                                for achieve in range(len(achieves)):
                                    for win_lose in range(len(attainments)):

                                        str_updns[cnt_updn] += ',' + str(closes[cnt_updn][height][win_lose][achieve]) + ','
                                        str_updns[cnt_updn] += ('0' if 0 == opens[cnt_updn][heights[height]] else
                                                     '{:.2f}'.format(closes[cnt_updn][height][win_lose][achieve] / opens[cnt_updn][heights[height]] * 100))
                                        if len(str_updns) - 2 == cnt_updn:
                                            str_updns[len(str_updns) - 1] += \
                                                ',' + str(closes[0][height][win_lose][achieve] + closes[1][height][win_lose][achieve]) + ','
                                            str_updns[len(str_updns) - 1] += ('0' if 0 == opens[0][heights[height]] + opens[1][heights[height]] else
                                                     '{:.2f}'.format((closes[0][height][win_lose][achieve] + closes[1][height][win_lose][achieve]) /
                                                                     (opens[0][heights[height]] + opens[1][heights[height]]) * 100))

                    str_years[i].append(''.join(str(forecasts[i][k])[:7].replace('-', '|')+ updns[u] + str_updns[u] + '\n'
                                                for u in range(len(str_updns))))
                    window.close()

                str_updns_total = ['', '', '']
                for c in range(len(curs)):

                    opens = []
                    closes = []

                    for cnt_updn in range(len(str_updns_total) - 1):
                        cnt1 = cnt_updn + 1
                        cnt3 = cnt_updn + 3

                        str_updns_total[cnt_updn] += ','
                        if len(str_updns_total) - 2 == cnt_updn:
                            str_updns_total[len(str_updns_total) - 1] += ',' + str(totals[c][0])

                        opens.append(totals[c][cnt1])
                        closes.append(totals[c][cnt3])

                        for height in range(len(heights)):

                            str_updns_total[cnt_updn] += ',' + str(opens[cnt_updn][heights[height]]) + ',' \
                                                         + '{:.2f}'.format(opens[cnt_updn][heights[height]] / totals[c][0] * 100)
                            if len(str_updns_total) - 2 == cnt_updn:
                                str_updns_total[len(str_updns_total) - 1] += \
                                    ',' + str(opens[0][heights[height]] + opens[1][heights[height]]) + ',' \
                                    + '{:.2f}'.format((opens[0][heights[height]] + opens[1][heights[height]]) / totals[c][0] * 100)

                            for achieve in range(len(achieves)):
                                for win_lose in range(len(attainments)):

                                    str_updns_total[cnt_updn] += ',' + str(closes[cnt_updn][height][win_lose][achieve]) + ','
                                    str_updns_total[cnt_updn] += ('0' if 0 == opens[cnt_updn][heights[height]] else
                                                            '{:.2f}'.format(closes[cnt_updn][height][win_lose][achieve] / opens[cnt_updn][heights[height]] * 100))
                                    if len(str_updns_total) - 2 == cnt_updn:
                                        str_updns_total[len(str_updns_total) - 1] += \
                                            ','+ str(closes[0][height][win_lose][achieve] + closes[1][height][win_lose][achieve]) + ','
                                        str_updns_total[len(str_updns_total) - 1] += \
                                            ('0' if 0 == opens[0][heights[height]] + opens[1][heights[height]] else
                                             '{:.2f}'.format((closes[0][height][win_lose][achieve] + closes[1][height][win_lose][achieve]) /
                                                             (opens[0][heights[height]] + opens[1][heights[height]]) * 100))

                str_years[i].insert(0, ''.join(str(year_target - 1 + i) + updns[u] + str_updns_total[u] + '\n'
                                               for u in range(len(str_updns_total))))
                run_time = com.time_end(start_time)
                total_time += run_time

                com.log(str(year_target - 1 + i) + ' 作成完了(' + com.conv_time_str(total_time) + ')')

            out_path = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'anomaly/')

            with open(out_path + 'ShakayMado' + '.csv', 'w') as out:
                out.write('Time,' + cols + '\n' + ''.join(''.join([updn for updn in years]) for years in str_years))

        except Exception as e:
            return 'マド空け編集でエラーが発生しました。\n' + str(e)
        finally:
            try: out.close()
            except: pass

        com.log('マド空け編集完了(' + com.conv_time_str(total_time) + ')')
        return ''

    # アノマリ〜編集各種実行
    def _edit_anomaly(self):

        inputs = com.input_box('アノマリ〜編集 開始しますか？', '開始確認', [
            ['対象年', int(com.str_time()[:4])], ['モデル期間', 15]])
        if inputs[0] <= 0:
            return

        year_target = int(inputs[1][0])

        try:
            window = com.progress('編集データ取得中', ['', 1], interrupt=True)
            event, values = window.read(timeout=0)

            con = my_sql.MySql('fx_history')
            if con.cnx is None:
                com.dialog('DB接続エラーが発生しました。', 'DB接続エラー発生', lv='W')
                return

            h_gotobe = {}
            h_window = {}

            tables = con.free('SHOW TABLES')
            str_range = ' WHERE \'' + str(year_target - int(inputs[1][1]) - 2) + '-01-01\' <= Time'\
                        + ' AND Time <= \'' + str(year_target - 1) + '-12-31\''

            for i in range(len(tables)):
                h_window[tables[i][0]] = con.free(
                    'SELECT * FROM ' + tables[i][0] + str_range + ' AND WEEKDAY(Time) < 2')
                if tables[i][0].startswith('z_'):
                    continue
                h_gotobe[tables[i][0]] = con.free(
                    'SELECT * FROM ' + tables[i][0] + str_range + ' AND WEEKDAY(Time) < 5'
                    + ' AND (RIGHT(LEFT(Time, 10), 1) IN(\'4\', \'5\', \'9\', \'0\')'
                    + ' OR \'31\' = RIGHT(LEFT(Time, 10), 2))')

            dfs = [[], []]
            for i in range(len(dfs)):
                for span in ['H', 'D', 'M', 'W']:

                    files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/') + '_stat/????' + span + '.csv')
                    files = sorted(files)

                    try:
                        years = [year for year in range(year_target - int(inputs[1][1]) - 2 + i, year_target - 1 + i)]
                        cnt = 0
                        while cnt < len(files):
                            if int(files[cnt].split('/')[-1].replace(span + '.csv', '')) in years:
                                cnt += 1
                            else:
                                del files[cnt]
                    except:
                        pass

                    df = pd.read_csv(files[0])
                    if 1 < len(files):
                        for k in range(1, len(files)):
                            df = pd.concat([df, pd.read_csv(files[k])])

                    df = df.reset_index(drop=True)
                    dfs[i].append(df)

            dfs.append(dfs[len(dfs) - 1])
            window.close()

        except Exception as e:
            com.dialog('エラーが発生しました。\n' + str(e), 'データ取得エラー発生', lv='W')
            return
        finally:
            con.close()

        window = com.progress('予測編集中', ['', 1], interrupt=True)
        event, values = window.read(timeout=0)

        err_msg = self._edit_normal(inputs, dfs)
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return
        window.close()

        err_msg = self._edit_gotobe(inputs, dfs, h_gotobe)
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        err_msg = self._edit_shakay_mado(inputs, dfs, h_window)
        if err_msg is None:
            return
        elif len(err_msg):
            com.dialog(err_msg, 'エラー発生', lv='W')
            return

        com.dialog('アノマリ〜編集が完了しました。', 'アノマリ〜編集完了')

    # CSV ⇨ JS変換
    def _conv_csv_js(self):
        io_path = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'anomaly/')
        files = glob.glob(io_path + '*.csv')
        files = sorted(files)

        value_year = ''
        data_year = {}
        cnt = 0

        try:
            for file in files:

                df = pd.read_csv(file)
                file_name = file.split('/')[-1].split('\\')[-1].replace('.csv', '')

                info = file_name + ' (' + str(cnt) + ' / ' + str(len(files)) + ')'
                window = com.progress('CSV ⇨ JS変換中', [info, len(files)])
                event, values = window.read(timeout=0)
                window[info + '_'].update(cnt)
                cnt += 1

                file_name = io_path + file_name
                data_other = {}
                time_values = ''

                for i in range(len(df)):

                    for key in df:

                        if 0 <= key.find('Unnamed'):
                            continue

                        if 'Time' == key:
                            time = str(df.at[df.index[i], key])
                            time_value = ('' if 0 == len(time_values) or 0 <= file_name.find('Year') else '\n  },')
                            time_value += '\n  "' + (time.split(' ')[0] if 0 <= file_name.find('Year') else time) + '": {'
                            time_values += time_value
                            continue

                        if  key.startswith('X_') or key.startswith('Z_'):
                            str_key = key.replace('X_', '').replace('Z_', '')
                        else:
                            str_key = key

                        if key == str_key:
                            name_key = (key if 0 == str_key.count('_') else key[: key.find('_', 1)])
                        else:
                            name_key = (key if 0 == str_key.count('_') else key[: key.find('_', 2)])

                        if 0 < str_key.count('_'):
                            if 0 < file_name.count('Year'):

                                str_span = key.split('_')[1 if key == str_key else 2]

                                if 1 == str_key.count('_'):

                                    value = '\n    "' + str_span \
                                            + '": {\n      "Count": "' + str(df.at[df.index[i], key]) + '"'
                                    try:
                                        data_year[name_key] += \
                                            '\n    },' + ('\n  },' + time_value if 'D' == str_span else '') + value
                                    except:
                                        data_year[name_key] = time_value + value

                                else:
                                    data_year[name_key] += \
                                        ',\n      "' + key[key.find('_', 1 if key == str_key else 2) + 1: key.rfind('_')] \
                                        + '": "' + str(df.at[df.index[i], key]) + '"'
                            else:
                                data_other[name_key] += ',\n    "' + key[key.find('_', 1 if key == str_key else 2) + 1:] \
                                                 + '": "' + str(df.at[df.index[i], key]) + '"'

                        else:
                            try:
                                data_other[name_key] += time_value + '\n    "Count": "' + str(df.at[df.index[i], key]) + '"'
                            except:
                                data_other[name_key] = time_value + '\n    "Count": "' + str(df.at[df.index[i], key]) + '"'

                if 0 == file_name.count('Year'):
                    with open(file_name + '.js', 'w') as out:
                        out.write('\n'.join('const ' + cur + '_' + file_name.split('/')[-1] + ' = {' + data_other[cur] + '\n  }\n}' for cur in data_other))

                window.close()

            with open(io_path + '/Days.js', 'w') as out:
                out.write('\n'.join('const ' + cur + ' = {' + data_year[cur] + '\n    }\n  }\n}' for cur in data_year))

        finally:
            try: window.close()
            except: pass

        com.dialog('CSV ⇨ JS変換が完了しました。', 'CSV ⇨ JS変換完了')


def _get_start_end(data, inputs):

    start_num = -1
    end_num = -1

    for k in range(0, len(data)):
        rows = data[k].split(',')

        if -1 == start_num:
            if int(rows[0][:4]) == int(inputs[1][0]):
                start_num = k

        if 0 < len(data[k]) and 2 < len(data[k].split(',')):
            end_num = k

    return start_num, end_num


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
