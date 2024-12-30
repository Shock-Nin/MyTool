#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from common import my_sql
from const import cst

import glob

PATHS = ['H1', 'MTF/H4', 'MTF/D1']
MTF_INPUTS = [['SMA', 5, 25, 50, 100]]

RENAME_CSV = {
    'JPNIDXJPY': 'z_jn',
    'USA30IDXUSD': 'z_dj',
    'USA500IDXUSD': 'z_sp',
    'USATECHIDXUSD': 'z_nq',
    'XAUUSD': 'z_gold',
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

    def _insert_db(self):
        inputs = com.input_box('DBヒストリカル更新 開始しますか？', '開始確認', [['対象年', int(com.str_time()[:4]) - 1]])
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

                window = com.progress('H1ヒストリカル INSERT中', [files[i].split('/')[-1], len(files)], interrupt=True,)
                event, values = window.read(timeout=0)

                window[files[i].split('/')[-1] + '_'].update(i)
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
                com.log(files[i].replace('\\', '/').split('/')[-1]
                        + '作成完了(' + com.conv_time_str(run_time) + ') ' + files[i])
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

    def _edit_mtf(self):

        inputs = com.input_box('開始しますか？', '開始確認', MTF_INPUTS)
        if inputs[0] <= 0:
            return

        files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'Trender') + '/H1_??????.csv')
        total_time = 0

        window = com.progress('MTFデータ作成中', [files[0].split('/')[-1], len(files)], interrupt=True)
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
                latest_h4 = -1

                out_d1 = ''
                hi_d1 = 0
                lo_d1 = 9999999
                count_d1 = 0

                for k in range(1, len(data) - 1):
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

                    if (k == len(data) - 2 or 0 == int(data[k + 1].split(',')[1]) % 4
                            or (0 != latest_h4 and 1 == int(data[k + 1].split(',')[1]))):

                        if not (0 == latest_h4 and int(op_hour_h4) < 4):
                            out_h4 += str(rows[0]) + ',' + ('00' if int(op_hour_h4) < 4 else str(op_hour_h4)) + ','
                            out_h4 += str(op_h4) + ',' + str(hi_h4) + ',' + str(lo_h4) + ',' + rows[5] + '\n'

                        count_h4 = 0
                        hi_h4 = 0
                        lo_h4 = 9999999
                        latest_h4 = int(op_hour_h4)

                    if k == len(data) - 2 or int(rows[0]) != int(data[k + 1].split(',')[0]):
                        out_d1 += str(rows[0]) + ',-,'
                        out_d1 += str(op_d1) + ',' + str(hi_d1) + ',' + str(lo_d1) + ',' + rows[5] + '\n'

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
                        out += ','.join(['{:.6f}'.format(ma) for ma in ma_lists]) + '\n'

                    open(cst.HST_PATH[cst.PC].replace('\\', '/') + 'Trender/Calc/' +
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
