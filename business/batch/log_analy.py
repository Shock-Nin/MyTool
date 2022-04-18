#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
バッチ
解析用ログ編集、DB登録
"""
from common import com
from const import cst
from common import my_sql

import os
import datetime

OUT_IP = cst.IP_LIST + ['133.32.']
TARGET_LOGS = ['cook', 'saya365', 'Log_Liberty']
TARGET_TABLES = ['cook_access', 'fx_saya365_access', 'fx_saya365_input', 'liberty_access']


class LogAnaly:

    def __init__(self, job):
        self.myjob = job
        self.is_batch = ('Batch' == job)

    def get_log(self):

        # 前日をセット
        today = datetime.datetime.now()
        today -= datetime.timedelta(days=1)

        try:
            # SQL実行
            cnx = my_sql.MySql('access')

            for fold in TARGET_LOGS:
                file = cst.TEMP_PATH[cst.PC] + (
                    '' if 'Win' == cst.PC else 'test_log/') + fold + '/' + today.strftime('%Y%m%d') + '.log'

                if os.path.exists(file):
                    com.log('解析対象ログ: ' + file.replace(cst.TEMP_PATH[cst.PC], ''))

                    with open(file, 'r', encoding='utf8') as read_file:
                    
                        if TARGET_LOGS[0] == fold:
                            self._analy_cook(cnx, read_file)
                            
                        elif TARGET_LOGS[1] == fold:
                            self._analy_saya(cnx, read_file)
                            
                        elif TARGET_LOGS[2] == fold:
                            self._analy_liberty(cnx, read_file)

        except Exception as e:
            com.log('解析用ログ編集エラー発生: ' + str(e), 'E')
            return False

        finally:
            try: cnx.close()
            except: pass

        com.log('Insert完了')
        return True

    # ブログの解析用ログ編集
    def _analy_cook(self, cnx, read_file):

        columns = ['Time', 'IP', 'Agent', 'Browser', 'Page', 'Category1', 'Category2']
        values = []

        for txt in read_file.read().split('\n'):
            if 0 == len(txt):
                break

            col = txt.split('\t')
            if col[3].find('[') < 0:
                continue
            if 0 <= col[3].find('エラー'):
                continue
            if 0 <= col[4].find('管理画面'):
                continue
            if not _check_ip(col[2]):
                continue

            val = [col[0], col[2].strip(), col[3][:col[3].find('[')], col[3][col[3].find('[') + 1: -1]]

            if col[4].find(' : ') < 0:
                val.append(col[4])
                val.append('')
                val.append('')
            else:
                val.append(col[4][col[4].find(' : ') + 3:])

                category = col[4][:col[4].find(' : ')]
                if category.find('-') < 0:
                    val.append(category)
                    val.append('')
                else:
                    val.append(category.split('-')[0])
                    val.append(category.split('-')[1])

            values.append(val)

        # SQL実行
        if 0 < len(values):
            if cnx.insert(columns, values, TARGET_TABLES[0]):
                cnx.commit()
            else:
                cnx.rollback()
                return False

        return True

    # サヤ取りの解析用ログ編集
    def _analy_saya(self, cnx, read_file):

        columns1 = ['Time', 'IP', 'Agent', 'Browser', 'Name']
        columns2 = ['Time', 'Name', 'Main', 'Simu', 'Test']
        values1 = []
        values2 = []

        for txt in read_file.read().split('\n'):
            if 0 == len(txt):
                break

            # 対象外IPを除外
            col = txt.split('\t')
            if not _check_ip(col[2]):
                continue

            if 0 <= txt.find('ログイン') or 0 <= txt.find('Free]'):
                val1 = [col[0], col[2].strip()]

                if 0 < txt.find('Free]'):
                    ary = col[3].split(' : ')
                    val1.append(ary[1][:ary[1].find('[')])
                    val1.append(ary[1][ary[1].find('[') + 1: len(ary[1]) - 1])
                    val1.append(ary[0])
                else:
                    val1.append(col[7][:col[7].find('[')])
                    val1.append(col[7][col[7].find('[') + 1: len(col[7]) - 1])
                    val1.append(col[4])

                values1.append(val1)

            if txt.find('ログイン') < 0 <= txt.find(' ⇒ '):
                val2 = [col[0], col[4]]

                if 'Main' == col[3][0: 4]:
                    val2.append(col[5].strip())
                    val2.append('')
                    val2.append('')

                elif 'Simu' == col[3][0: 4]:
                    val2.append('')
                    val2.append(col[5].strip())
                    val2.append('')

                elif 'Test' == col[3][0: 4]:
                    val2.append('')
                    val2.append('')
                    val2.append(col[5].strip())

                values2.append(val2)

        # SQL実行
        is_insert = True
        if 0 < len(values1):
            if cnx.insert(columns1, values1, TARGET_TABLES[1]):
                cnx.commit()
            else:
                cnx.rollback()
                is_insert = False

        if 0 < len(values2):
            if cnx.insert(columns2, values2, TARGET_TABLES[2]):
                cnx.commit()
            else:
                cnx.rollback()
                is_insert = False

        return is_insert

    # 公人サイトの解析用ログ編集
    def _analy_liberty(self, cnx, read_file):

        columns = ['Time', 'Ip', 'City', 'Hostname', 'Browser', 'Action']
        values = []

        for txt in read_file.read().split('\n'):
            if 0 == len(txt):
                break
            if txt.fibnd('{') < 0:
                break

            txt = txt.replace('}', '')
            txt = txt.replace('{', ';')

            row = txt.split(';')
            cols = row[1].split(',')

            # 対象外IPを除外
            is_check_ip = False
            for col in cols:
                ary = col.replace('\"', '').split(':')
                if 'ip' == ary[0]:
                    is_check_ip = _check_ip(ary[1])

            if not is_check_ip:
                continue

            val = [row[0]]

            for col in cols:
                ary = col.replace('\"', '').split(':')

                if ary[0] in ['ip', 'city', 'hostname', 'agent', 'browser']:
                    val.append(ary[1])

                elif 'action' == ary[0]:
                    if ary[1] is None:
                        val.append('')
                    else:
                        val.append(ary[1])

            values.append(val)

        # SQL実行
        if 0 < len(values):
            if cnx.insert(columns, values, TARGET_TABLES[3]):
                cnx.commit()
            else:
                cnx.rollback()
                return False
            
        return True


# 自IP除外
def _check_ip(ip):
    for chk in OUT_IP:
        if 0 <= ip.find(chk):
            return False
    return True
