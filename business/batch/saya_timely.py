#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
バッチ
くりっく365のリアルレート(ブラウザ)取得、DB登録
"""
from common import com
from const import cst
from common import my_sql
from common import web_driver

TARGET_TABLES = ['rate_new']


class SayaTimely:

    def __init__(self, job):
        self.myjob = job
        self.is_batch = ('Batch' == job)

    def get_web(self):

        rates = []
        try:
            # ウェブ操作スタート
            wd = web_driver.driver(headless=self.is_batch)
            if wd is None:
                com.log('WebDriverエラー', 'E')
                return

            wd.get(cst.RATE_REAL)
            com.sleep(3)

            html = wd.page_source
            html = html[html.find('fx_api01'): html.find('対外貨通貨ペア')]
            html = html[html.find('<'): html.find('</tbody>')]

            while 0 < html.find('/JPY </a>'):
                html = html[html.find('/JPY </a>') + 10:]
                txt = html
                txt = txt[txt.find('<td'):]
                if 0 <= html.find('/JPY </a>'):
                    txt = txt[:html.find('/JPY </a>')]

                txt = txt[txt.find('>') + 1:]
                if 0 == txt.find('<img'):
                    txt = txt[txt.find('<img') + 1:]
                    txt = txt[txt.find('>') + 1:]

                rates.append(txt[:txt.find('<')])
                txt = txt[txt.find('<td'):]
                txt = txt[txt.find('>') + 1:]
                if 0 == txt.find('<img'):
                    txt = txt[txt.find('<img') + 1:]
                    txt = txt[txt.find('>') + 1:]
                rates.append(txt[:txt.find('<')])

                if 0 <= txt.find('　'):
                    html = html[html.find('/JPY </a>') + 10:]
            
        except Exception as e:
            com.log('365リアルWeb取得エラー発生: ' + str(e), 'E')
            return

        finally:
            try: wd.quit()
            except: pass

        return self._insert_sql(rates)

    def _insert_sql(self, rates):

        if 0 == len(rates):
            return False

        try:
            errs = ''
            err_count = 0

            for i in range(0, len(cst.CURRNCYS_365) * 2):
                if len(rates[i]) <= 2:
                    errs += (', ' if 0 < err_count else '') + cst.CURRNCYS_365[int(round((i + 1) / 2))] + '("－")'
                    err_count += 1

            if 0 < err_count:
                com.log('365リアルSQL更新回避', 'E')
                return False

            # SQL用項目列作成
            columns = [('USD' if cur in ['JPY'] else '') + cur +
                       ('' if cur in ['JPY'] else 'JPY') for cur in cst.CURRNCYS_365]
            columns.insert(0, 'DATE')

            # SQL用データ作成
            sells = [com.str_time()]
            buys = [com.str_time()]

            for i in range(0, len(rates)):
                if i % 2 == 0:
                    sells.append(rates[i])
                else:
                    buys.append(rates[i])

            # SQL実行
            cnx = my_sql.MySql('fx_saya365')
            is_sql = cnx.delete(TARGET_TABLES[0], 'DATE <> \'' + com.str_time() + '\'')
            if is_sql:
                is_sql = cnx.insert(columns, [sells], TARGET_TABLES[0])
            if is_sql:
                is_sql = cnx.insert(columns, [buys], TARGET_TABLES[0])

            # コミットで確定
            if is_sql:
                cnx.commit()
            else:
                cnx.rollback()
                return False

        except Exception as e:
            com.log('365リアルSQL更新エラー発生: ' + str(e), 'E')
            return False

        finally:
            try: cnx.close()
            except: pass

        return True
