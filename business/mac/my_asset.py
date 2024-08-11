#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from common import my_sql
from common import web_driver
from const import cst
from business.multiple.web_login import WebLogin

import datetime

TARGET_TABLES = ['asset_history']


class MyAsset:

    def __init__(self, job):
        self.myjob = job
        self.cnx = None

    def do(self):

        try:

            # 7時未満はNG
            if datetime.datetime.now().hour < 7:
                com.dialog('時間外、7時未満です。', '時間外', 'W')
                return

            # DB接続
            self.cnx = my_sql.MySql('data_my')

            # 最新日のデータ取得
            before = self.cnx.select('*', TARGET_TABLES[0], '', 'ORDER BY 日付 DESC LIMIT 1')

            # 本日のデータ取得済みなら中断
            if com.str_time()[:10] == datetime.datetime.strftime(before[1][0], '%Y-%m-%d'):
                com.dialog('本日は取得済です。', '本日取得済', 'W')
                return

        # 最後はDBを閉じる
        finally:
            try: self.cnx.close()
            except: pass

        if com.question(self.myjob + ' 開始しますか？', '開始確認') <= 0:
            return

        start_time = com.time_start()
        total_time = 0

        com.log('資産チェック開始')

        # 取得サイト情報をセット
        targets = cst.MENU_CSV['Web']
        targets = targets[('資産' == targets['Type'])]

        try:
            # # ViewCard取得
            # target = targets[('ViewCard' == targets['Name'])]
            # vcard, wd1 = self._get_view_card(target)
            # if vcard is None:
            #     return

            vcard = [0, 0, 0, 0]

            # 楽天カード取得
            target = targets[('楽天カード' == targets['Name'])]
            rcard, wd2 = self.__get_rakuten_card(target)
            if rcard is None:
                return

            banks = [0]

            # # 三井住友銀行取得
            # target = targets[('三井住友' == targets['Name'])]
            # result, wd3 = self._get_smbc_bank(target)
            # if result is None:
            #     return
            # else:
            #     banks.append(result)

            # 三菱UFJ銀行取得
            target = targets[('三菱UFJ' == targets['Name'])]
            result, wd4 = self.__get_mufg_bank(target)
            if result is None:
                return
            else:
                banks.append(result)

            # 楽天銀行取得
            target = targets[('楽天銀行' == targets['Name'])]
            result, wd5 = self.__get_rakuten_bank(target)
            if result is None:
                return
            else:
                banks.append(result)

            # JREBANK取得
            target = targets[('JREBANK' == targets['Name'])]
            result, wd6 = self.__get_jre_bank(target)
            if result is None:
                return
            else:
                banks.append(result)

            run_time = com.time_end(start_time)
            total_time += run_time
            start_time = com.time_start()
            com.log('資産情報取得完了(' + com.conv_time_str(run_time) + '): ')

            # 取得データと前回データの差分計算
            is_change, layout, columns, values = _edit_data(before, vcard, rcard, banks)

            # DB接続
            self.cnx = my_sql.MySql('data_my')

            # 取得データを登録
            if self.cnx.insert(columns, values, TARGET_TABLES[0]):
                self.cnx.commit()
            else:
                self.cnx.rollback()
                com.dialog('SQLのINSERTに失敗しました。', 'SQLエラー', 'E')
                return

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log('SQLのINSERT完了(' + com.conv_time_str(run_time) + '): ')

        # 最後はDBを閉じる
        finally:
            try: self.cnx.close()
            except: pass

        com.dialog_cols(com.str_time()[:10] + '(前回 ' + datetime.datetime.strftime(before[1][0], '%Y-%m-%d') +
                        ')\n完了しました。(' + com.conv_time_str(total_time) + ')', layout, ['l', 'r', 'c', 'r'], self.myjob)

    # Viewカード
    def __get_view_card(self, target):

        # ログイン
        results = []
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得(未確定・1月前・2月前・3月前)
        try:
            results.append(web_driver.find_element(wd, 'LblSumUseValue').text.replace(',', ''))
        except Exception as e:
            results.append(0)
        for i in range(1, 4):
            try:
                web_driver.find_element(wd, 'vucV0300MonthList_LiClaimYm' + str(i)).click()
                com.sleep(1)
                results.append(web_driver.find_element(wd, 'div#payment td strong').text.replace(',', ''))
            except:
                try:
                    web_driver.find_element(wd, 'LnkClaimYm' + str(i)).click()
                    com.sleep(1)
                    results.append(web_driver.find_element(wd, 'div#payment td strong').text.replace(',', ''))
                except Exception as e:
                    com.log('WebDriverエラー: Viewカード, ' + str(e), 'E')
                    com.dialog('Viewカードで、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
                    return None, None
        return results, wd

    # 楽天カード
    def __get_rakuten_card(self, target):

        # ログイン
        results = []
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得(未確定・1月前・2月前・3月前)
        try:
            for i in range(0, 2):
                wd.get('https://www.rakuten-card.co.jp/e-navi/members/statement/index.xhtml?tabNo=' + str(i))
                com.sleep(1)
                try:
                    results.append(web_driver.find_element(wd, 'span.stmt-u-font-roboto').text.replace(',', ''))
                except:
                    results.append('0')
        except Exception as e:
            com.log('WebDriverエラー: 楽天カード, ' + str(e), 'E')
            com.dialog('楽天カードで、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return results, wd

    # 三井住友
    def __get_smbc_bank(self, target):

        # ログイン
        result = ''
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得
        try:
            result = web_driver.find_element(wd, 'ryudoAccountBalance').text.replace(',', '')
        except Exception as e:
            com.log('WebDriverエラー: 三井住友, ' + str(e), 'E')
            com.dialog('三井住友で、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return result, wd

    # 三菱UFJ
    def __get_mufg_bank(self, target):

        # ログイン
        result = ''
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得
        try:
            result = web_driver.find_element(
                wd, '/html/body/app-root/app-lgpu01-wf/div/main/div/app-lgpu01-lg0002-m00-c01/form/section/div/div[1]/div/div[2]/section[1]/a/div[1]/div[3]/span[1]') \
                .text.replace(',', '').replace('円', '')
        except Exception as e:
            com.log('WebDriverエラー: 三菱UFJ, ' + str(e), 'E')
            com.dialog('三菱UFJで、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return result, wd

    # 楽天銀行
    def __get_rakuten_bank(self, target):

        # ログイン
        result = ''
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得
        try:
            com.sleep(1)
            result = web_driver.find_element(
                wd, '//*[@id="lyt-deposit"]/div/div[2]/div/div[3]/div[1]/table/tbody/tr/td/span[1]') \
                .text.replace(',', '')
        except Exception as e:
            com.log('WebDriverエラー: 楽天銀行, ' + str(e), 'E')
            com.dialog('楽天銀行で、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return result, wd

    # JREBANK
    def __get_jre_bank(self, target):

        # ログイン
        result = ''
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得
        try:
            com.sleep(2)
            result = web_driver.find_element(wd, 'amount-displayed').text.replace(',', '')
        except Exception as e:
            com.log('WebDriverエラー: JREBANK, ' + str(e), 'E')
            com.dialog('JREBANKで、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return result, wd

# ダイヤログ用差分とINSERTのSQLデータ作成
def _edit_data(before, vcard, rcard, banks):

    is_change = False
    layout = [['Viewカード', '楽天カード', '三井住友', '三菱UFJ', '楽天銀行', 'JREBANK'], [], [], []]

    # 日付
    columns = [before[0][0]]
    values = [com.str_time()[:10]]

    # Viewカード未確定
    # __append_data(before[1][1], vcard[0], before[0][1], is_change, layout, columns, values)

    # 楽天カード未確定
    __append_data(before[1][2], rcard[0], before[0][2], is_change, layout, columns, values)

    af_vcard1 = vcard[1]
    columns.append(before[0][3])
    values.append(af_vcard1)
    af_rcard1 = rcard[1]
    columns.append(before[0][4])
    values.append(af_rcard1)

    # 三井住友
    # __append_data(before[1][9], banks[0], before[0][9], is_change, layout, columns, values)

    # 三菱UFJ
    __append_data(before[1][10], banks[1], before[0][10], is_change, layout, columns, values)

    # 楽天銀行
    __append_data(before[1][11], banks[2], before[0][11], is_change, layout, columns, values)

    # JREBANK
    __append_data(before[1][12], banks[3], before[0][12], is_change, layout, columns, values)

    return is_change, layout, columns, [values]

def __append_data(before, now, col, is_change, layout, columns, values):

    columns.append(col)
    layout[1].append(format(before, ','))
    if int(before) == int(now):
        layout[2].append('')
        layout[3].append('')
        values.append(before)
    else:
        is_change = True
        layout[2].append('→')
        layout[3].append(format(int(now), ','))
        values.append(now)

    return is_change, layout, columns, values
