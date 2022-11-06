#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
"""
バッチ
くりっく365の日足レート(CSV)取得、DB登録
"""
from common import com
from const import cst
from common import my_sql

import requests
import datetime

TARGET_TABLES = ['rate', 'swap']


class SayaDaily:

    def __init__(self, job):
        self.myjob = job
        self.is_batch = ('Batch' == job)

    def get_csv(self):
        try:
            # SQL実行
            cnx = my_sql.MySql('fx_saya365')
            last_date = cnx.free('SELECT MAX(DATE) FROM ' + TARGET_TABLES[0])[0]

            # 前日をセット
            today = datetime.datetime.now()
            today -= datetime.timedelta(days=1)

            # 最終更新 +1 日をセット
            last_date = str(last_date[0].year) + \
                        ('0' if last_date[0].month< 10 else '') + str(last_date[0].month) + \
                        ('0' if last_date[0].day < 10 else '') + str(last_date[0].day)
            last_date = datetime.datetime.strptime(last_date, '%Y%m%d')
            last_date = last_date

            # 更新の対象日数
            days_diff = (today - last_date).days

            if 0 == days_diff:
                com.log('365日足取得不要: ' + datetime.datetime.strftime(last_date, '%Y%m%d') + ' 取得済')

            # SQL用項目列作成
            columns = [('USD' if cur in ['JPY'] else '') + cur +
                       ('' if cur in ['JPY'] else 'JPY') for cur in cst.CURRENCIES_365]
            columns.insert(0, 'DATE')

            # 更新対象がある間繰り返し
            for i in range(1, days_diff + 1):

                # 最終更新 +日をセット
                count_date = last_date + datetime.timedelta(days=i)
                target_ymd = datetime.datetime.strftime(count_date, '%Y-%m-%d')

                try:
                    # くりっく365公式サイトから、終値とスワップを取得
                    data = self._download(target_ymd.replace('-', ''))

                    com.log('Last ' + datetime.datetime.strftime(last_date, '%Y%m%d') + ' → ' +
                            'Target ' + datetime.datetime.strftime(count_date, '%Y%m%d') + ' → ' +
                            'Today ' + datetime.datetime.strftime(today, '%Y%m%d'))
                    if data is None:
                        continue
                    elif 0 == len(data):
                        com.log('365日足取得(' + target_ymd + ')不在')
                        continue

                    # SQL用データ作成
                    rates = [target_ymd]
                    swaps = [target_ymd]

                    for key in data:
                        rates.append(data[key][0])
                        swaps.append(data[key][1])

                    # SQL実行
                    is_sql = cnx.insert(columns, [rates], TARGET_TABLES[0])
                    if is_sql:
                        is_sql = cnx.insert(columns, [swaps], TARGET_TABLES[1])

                    # コミットで確定
                    if is_sql:
                        cnx.commit()
                    else:
                        cnx.rollback()

                except Exception as e:
                    com.log('365日足取得(' + target_ymd + ')エラー発生: ' + str(e), 'E')

        except Exception as e:
            com.log('365日足取得エラー発生: ' + str(e), 'E')
            return False

        finally:
            try: cnx.close()
            except: pass

        return True

    # くりっく365公式サイトから、終値とスワップを取得
    def _download(self, target_ymd):
        data = {}
        try:
            # くりっく365のURLからCSVダウンロード
            file = requests.get(cst.RATE_CSV + target_ymd + '.CSV')
            for chunk in file.iter_content(100000):

                rows = str(chunk).split('\n')[0]
                curs = rows.split('\\nD01')

                for i in range(1, len(curs)):

                    cols = curs[i].split(',')
                    if 0 <= cols[3].find('/USD'):
                        break

                    data[cols[3]] = [cols[14], cols[16]]

        except Exception as e:
            com.log('365日足取得(' + target_ymd + ')エラー発生: ' + str(e), 'E')
            return None

        return data


    # def _insert_sql(self, rates):
    #
    #         RateDTO rateDto = new RateDTO();
    #         rateDto.setDATE(cntDate);
    #         rateDto.setUSDJPY(list.get(0).get(1));
    #         rateDto.setEURJPY(list.get(1).get(1));
    #         rateDto.setGBPJPY(list.get(2).get(1));
    #         rateDto.setAUDJPY(list.get(3).get(1));
    #         rateDto.setCHFJPY(list.get(4).get(1));
    #         rateDto.setCADJPY(list.get(5).get(1));
    #         rateDto.setNZDJPY(list.get(6).get(1));
    #         rateDto.setZARJPY(list.get(7).get(1));
    #         rateDto.setTRYJPY(list.get(8).get(1));
    #         rateDto.setNOKJPY(list.get(9).get(1));
    #         rateDto.setHKDJPY(list.get(10).get(1));
    #         rateDto.setSEKJPY(list.get(11).get(1));
    #         rateDto.setMXNJPY(list.get(12).get(1));
    #         rateDto.setPLNJPY(list.get(13).get(1));
    #
    #         SwapDTO swapDto = new SwapDTO();
    #         swapDto.setDATE(cntDate);
    #         swapDto.setUSDJPY(list.get(0).get(2));
    #         swapDto.setEURJPY(list.get(1).get(2));
    #         swapDto.setGBPJPY(list.get(2).get(2));
    #         swapDto.setAUDJPY(list.get(3).get(2));
    #         swapDto.setCHFJPY(list.get(4).get(2));
    #         swapDto.setCADJPY(list.get(5).get(2));
    #         swapDto.setNZDJPY(list.get(6).get(2));
    #         swapDto.setZARJPY(list.get(7).get(2));
    #         swapDto.setTRYJPY(list.get(8).get(2));
    #         swapDto.setNOKJPY(list.get(9).get(2));
    #         swapDto.setHKDJPY(list.get(10).get(2));
    #         swapDto.setSEKJPY(list.get(11).get(2));
    #         swapDto.setMXNJPY(list.get(12).get(2));
    #         swapDto.setPLNJPY(list.get(13).get(2));
    #
    #         // SQL実行
    #         if (!con.insert(rateDto)) return false;
    #         if (!con.insert(swapDto)) return false;
    #     return true;
    # }
