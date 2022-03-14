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

        if com.question(self.myjob + ' 開始しますか？', '開始確認') <= 0:
            return

        start_time = com.time_start()
        total_time = 0

        com.log('資産チェック開始')

        # 取得サイト情報をセット
        targets = cst.MENU_CSV['Web']
        targets = targets[('資産' == targets['Type'])]

        try:
            # DB接続
            self.cnx = my_sql.MySql('data_my')

            # 最新日のデータ取得
            before = self.cnx.select('*', TARGET_TABLES[0], '', 'ORDER BY 日付 DESC LIMIT 1')

            # 本日のデータ取得済みなら中断
            if com.str_time()[:10] == datetime.datetime.strftime(before[1][0], '%Y-%m-%d'):
                com.dialog('本日は取得済です。', '本日取得済', 'W')
                return

            # ViewCard取得
            target = targets[('ViewCard' == targets['Name'])]
            vcard, wd1 = self._get_view_card(target)
            if vcard is None:
                return

            # 楽天カード取得
            target = targets[('楽天カード' == targets['Name'])]
            rcard, wd2 = self._get_rakuten_card(target)
            if rcard is None:
                return

            banks = []

            # 三井住友銀行取得
            target = targets[('三井住友' == targets['Name'])]
            result, wd3 = self._get_smbc_bank(target)
            if result is None:
                return
            else:
                banks.append(result)

            # 三菱UFJ銀行取得
            target = targets[('三菱UFJ' == targets['Name'])]
            result, wd4 = self._get_mufg_bank(target)
            if result is None:
                return
            else:
                banks.append(result)

            # 楽天銀行取得
            target = targets[('楽天銀行' == targets['Name'])]
            result, wd5 = self._get_rakuten_bank(target)
            if result is None:
                return
            else:
                banks.append(result)

            run_time = com.time_end(start_time)
            total_time += run_time
            start_time = com.time_start()
            com.log('資産情報取得完了(' + com.conv_time_str(run_time) + '): ')

            # 取得データと前回データの差分計算
            is_change, layout, columns, values = self._edit_data(before, vcard, rcard, banks)

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
    def _get_view_card(self, target):

        # ログイン
        results = []
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得(未確定・1月前・2月前・3月前)
        try:
            results.append(web_driver.find_element(wd, 'LblSumUseValue').text.replace(',', ''))
            for i in range(1, 4):
                web_driver.find_element(wd, 'vucV0300MonthList_LiClaimYm' + str(i)).click()
                com.sleep(1)
                results.append(web_driver.find_element(wd, 'div#payment td strong').text.replace(',', ''))
        except Exception as e:
            com.log('WebDriverエラー: Viewカード, ' + str(e), 'E')
            com.dialog('Viewカードで、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return results, wd

    # 楽天カード
    def _get_rakuten_card(self, target):

        # ログイン
        results = []
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得(未確定・1月前・2月前・3月前)
        try:
            for i in range(0, 4):
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
    def _get_smbc_bank(self, target):

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
    def _get_mufg_bank(self, target):

        # ログイン
        result = ''
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得
        try:
            result = web_driver.find_element(
                wd, '/html/body/div/main/form/section/div/div[1]/div/div[2]/section[1]/a/div[1]/div[3]/span[1]') \
                .text.replace(',', '').replace('円', '')
        except Exception as e:
            com.log('WebDriverエラー: 三菱UFJ, ' + str(e), 'E')
            com.dialog('三菱UFJで、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return result, wd

    # 楽天銀行
    def _get_rakuten_bank(self, target):

        # ログイン
        result = ''
        wd = WebLogin(self.myjob).do(target['Name'].values[0], target['URL'].values[0])
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return None, None

        # 金額取得
        try:
            com.sleep(1)
            result = web_driver.find_element(wd, '//*[@id="BALANCEINQUIRYBODYPERSONAL:FORM_HEAD:_idJsp343"]/span[2]') \
                .text.replace(',', '').replace('円', '')
        except Exception as e:
            com.log('WebDriverエラー: 楽天銀行, ' + str(e), 'E')
            com.dialog('楽天銀行で、WebDriverエラーが発生しました。\n' + str(e), 'WebDriverエラー', 'E')
            return None, None

        return result, wd

    # ダイヤログ用差分とINSERTのSQLデータ作成
    def _edit_data(self, before, vcard, rcard, banks):

        is_change = False
        layout = [['Viewカード', '楽天カード', '三井住友', '三菱UFJ', '楽天銀行'], [], [], []]

        # 日付
        columns = [before[0][0]]
        values = [com.str_time()[:10]]

        # Viewカード未確定
        bf_vcard0 = before[1][1]
        af_vcard0 = vcard[0]
        columns.append(before[0][1])
        layout[1].append(format(bf_vcard0, ','))
        if int(bf_vcard0) == int(af_vcard0):
            layout[2].append('')
            layout[3].append('')
            values.append(bf_vcard0)
        else:
            is_change = True
            layout[2].append('→')
            layout[3].append(format(int(af_vcard0), ','))
            values.append(af_vcard0)

        # 楽天カード未確定
        bf_rcard0 = before[1][2]
        af_rcard0 = rcard[0]
        columns.append(before[0][2])
        layout[1].append(format(bf_rcard0, ','))
        if int(bf_rcard0) == int(af_rcard0):
            layout[2].append('')
            layout[3].append('')
            values.append(bf_rcard0)
        else:
            is_change = True
            layout[2].append('→')
            layout[3].append(format(int(af_rcard0), ','))
            values.append(af_rcard0)

        af_vcard1 = vcard[1]
        columns.append(before[0][3])
        values.append(af_vcard1)
        af_rcard1 = rcard[1]
        columns.append(before[0][4])
        values.append(af_rcard1)

        af_vcard2 = vcard[2]
        columns.append(before[0][5])
        values.append(af_vcard2)
        af_rcard2 = rcard[2]
        columns.append(before[0][6])
        values.append(af_rcard2)

        af_vcard3 = rcard[3]
        columns.append(before[0][7])
        values.append(af_vcard3)
        af_rcard3 = rcard[3]
        columns.append(before[0][8])
        values.append(af_rcard3)

        # 三井住友
        bf_smbc = before[1][9]
        af_smbc = banks[0]
        columns.append(before[0][9])
        layout[1].append(format(bf_smbc, ','))
        if int(bf_smbc) == int(af_smbc):
            layout[2].append('')
            layout[3].append('')
            values.append(bf_smbc)
        else:
            is_change = True
            layout[2].append('→')
            layout[3].append(format(int(af_smbc), ','))
            values.append(af_smbc)

        # 三菱UFJ
        bf_mufg = before[1][10]
        af_mufg = banks[1]
        columns.append(before[0][10])
        layout[1].append(format(bf_mufg, ','))
        if int(bf_mufg) == int(af_mufg):
            layout[2].append('')
            layout[3].append('')
            values.append(bf_mufg)
        else:
            is_change = True
            layout[2].append('→')
            layout[3].append(format(int(af_mufg), ','))
            values.append(af_mufg)

        # 楽天銀行
        bf_rbank = before[1][11]
        af_rbank = banks[2]
        columns.append(before[0][11])
        layout[1].append(format(bf_rbank, ','))
        if int(bf_rbank) == int(af_rbank):
            layout[2].append('')
            layout[3].append('')
            values.append(bf_rbank)
        else:
            is_change = True
            layout[2].append('→')
            layout[3].append(format(int(af_rbank), ','))
            values.append(af_rbank)

        return is_change, layout, columns, [values]
