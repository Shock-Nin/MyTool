#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from common import my_sql
from const import cst

import glob
import pandas as pd

PATHS = ['H1', 'MTF/H4', 'MTF/D1']
MTF_INPUTS = [['SMA', 5, 25, 50, 100]]

RENAME_CSV = {
    # 'DOLLARIDX': 'usdidx',
    'XAUUSD': 'x_gold',
    'JPNIDXJPY': 'z_jn',
    'USA30IDXUSD': 'z_dj',
    'USA500IDXUSD': 'z_sp',
    'USATECHIDXUSD': 'z_nq',
}

class AnomalyHst:

    def __init__(self, function):
        self.function = function

    def do(self):
        getattr(self, '_' + self.function)()

    def _create_h1(self):
        if com.question('H1ヒストリカル編集 開始しますか？', '開始確認') <= 0:
            return

        files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/') + '/*.csv')
        total_time = 0

        try:
            for i in range(len(files)):
                data = open(files[i], 'r').read().split('\n')
                file = files[i].split('\\')[-1]

                window = com.progress('H1データ作成中', [file , len(files)], interrupt=True)
                event, values = window.read(timeout=0)

                window[file].update(file + ' (' + str(i) + ' / ' + str(len(files)) + ')')
                window[file + '_'].update(i)

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

                # open(files[i].replace('\\', '/').replace('history/', 'Trender/H1_'), 'w').write(out)
                open(files[i].replace('\\', '/').replace('history/', 'history_h1/'), 'w').write(out)

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

        return

    def _create_d1(self):
        if com.question('D1ヒストリカル編集 開始しますか？', '開始確認') <= 0:
            return

        files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/') + '_h1/*.csv')
        total_time = 0
        try:
            for i in range(len(files)):

                file = files[i].split('\\')[-1]
                window = com.progress('D1データ作成中', [file, len(files)], interrupt=True)
                event, values = window.read(timeout=0)

                window[file].update(file + ' (' + str(i) + ' / ' + str(len(files)) + ')')
                window[file + '_'].update(i)

                start_time = com.time_start()

                df = pd.read_csv(files[i].replace('\\', '/'), header=None)
                df.columns = ['Time', 'Hour', 'Open', 'High', 'Low', 'Close']

                df['Time'] = df['Time'].astype(str)
                df['Hour'] = df['Hour'].astype(str)
                df['Time'] = df['Time'].str.cat(df['Hour'], sep=' ')
                df['Time'] = pd.to_datetime(df['Time'], format='%Y%m%d %H')

                days = sorted(set(list(df['Time'].astype(str).str.slice_replace(start=10, stop=20))))
                rows =[]
                for day in days:
                    day_df = df[(day == df['Time'].astype(str).str.slice_replace(start=10, stop=20))].reset_index(drop=True)
                    rows.append([str(day).replace('-', ''), day_df.at[0, 'Open'], day_df['High'].max(), day_df['Low'].min(), day_df.at[len(day_df) - 1, 'Close']])

                df = pd.DataFrame(rows, columns = ['Time', 'Open', 'High', 'Low', 'Close'])
                df = df.set_index('Time')

                df.to_csv(files[i].replace('\\', '/') .replace('_h1', '_d1'), header=False)
                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(files[i].replace('\\', '/').split('/')[-1] +
                        '作成完了(' + com.conv_time_str(run_time) + ') ' + files[i])
                window.close()
        finally:
            try: window.close()
            except: pass

        com.log('D1作成完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('D1作成完了しました。(' + com.conv_time_str(total_time) + ')', 'D1作成完了')


    def _insert_db(self):
        inputs = com.input_box('DBヒストリカル更新 開始しますか？', '開始確認', [['対象年', 2003]])
        if inputs[0] <= 0:
            return

        files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/') + '_h1/*.csv')
        total_time = 0

        try:
            con = my_sql.MySql('fx_history')

            for i in range(len(files)):
                table = files[i].split('\\')[-1].replace('.csv', '')
                for key in RENAME_CSV:
                    if key == table:
                        table = RENAME_CSV[key]

                data = open(files[i], 'r').read().split('\n')

                file = files[i].split('\\')[-1]

                window = com.progress('H1ヒストリカル INSERT中', [file , len(files)], interrupt=True)
                event, values = window.read(timeout=0)

                window[file].update(file + ' (' + str(i) + ' / ' + str(len(files)) + ')')
                window[file + '_'].update(i)

                # con.delete(table, '')

                start_time = com.time_start()
                inserts = []
                for k in range(len(data) - 1):
                    rows = data[k].split(',')

                    if int(rows[0][:4]) < int(inputs[1][0]):
                        continue

                    inserts.append([rows[0][:4] + '-' + rows[0][4:6] + '-' + rows[0][6:] + ' '
                                    + ('0' if int(rows[1]) < 10 else '') + rows[1] + ':00:00',
                                    rows[2], rows[3], rows[4], rows[5]])

                    if k % 10000 == 0:
                        con.insert(['Time', 'Open', 'High', 'Low', 'Close'], inserts, table)
                        inserts = []

                if 0 < len(inserts):
                    con.insert(['Time', 'Open', 'High', 'Low', 'Close'], inserts, table)
                con.commit()

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(file + '作成完了(' + com.conv_time_str(run_time) + ') ' + files[i])
                window.close()
        except:
            con.rollback()

        finally:
            con.close()
            try:
                window.close()
            except:
                pass

        com.log('H1ヒストリカルINSERT完了(' + com.conv_time_str(total_time) + ')')
        com.dialog('H1ヒストリカルINSERT完了しました。(' + com.conv_time_str(total_time) + ')', 'H1データDB格納完了')

        return 0
