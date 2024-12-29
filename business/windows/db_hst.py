#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst
from common import my_sql

import glob

RENAME_CSV = {
    'JPNIDXJPY': 'z_jn',
    'USA30IDXUSD': 'z_dj',
    'USA500IDXUSD': 'z_sp',
    'USATECHIDXUSD': 'z_nq',
    'XAUUSD': 'z_gold',
}


class DbHst:
    def __init__(self, function):
        self.function = function

    def do(self):
        getattr(self, '_' + self.function)()

    def _update(self):
        inputs = com.input_box('DBヒストリカル更新 開始しますか？', '開始確認', [['対象年', int(com.str_time()[:4]) - 1]])
        if inputs[0] <= 0:
            return 0

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

                window = com.progress(
                    'ヒストリカル INSERT中',
                    [files[i].split('/')[-1], len(files)],
                    interrupt=True,
                )
                event, values = window.read(timeout=0)

                window[files[i].split('/')[-1] + '_'].update(i)
                start_time = com.time_start()

                inserts = []
                for k in range(len(data) - 1):
                    rows = data[k].split(',')
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

        com.log('ヒストリカルINSERT完了(' + com.conv_time_str(total_time) + ')')
        com.dialog(
            'ヒストリカルINSERT完了しました。(' + com.conv_time_str(total_time) + ')',
            'ヒストリカルINSERT完了',
        )

        return 0

    def _create(self):
        try:
            con = my_sql.MySql('fx_history')
            tables = con.free('SHOW TABLES')

            for i in range(len(tables)):
                window = com.progress('データ作成中', [tables[i][0], len(tables)], interrupt=True)
                event, values = window.read(timeout=0)

                print(tables[i][0])

        except:
            con.rollback()

        finally:
            con.close()
            try:
                window.close()
            except:
                pass
