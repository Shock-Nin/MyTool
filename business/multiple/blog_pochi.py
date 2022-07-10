#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst
from common import web_driver


class BlogPochi:

    def __init__(self, job):
        self.myjob = job
        self.is_batch = ('Batch' == job)

    def do(self):

        if not self.is_batch:
            if com.question(self.myjob + ' 開始しますか？', '開始確認') <= 0:
                return

        start_time = com.time_start()
        com.log('ブログクリック開始')
        err_msg = []

        menu = cst.MENU_CSV['PwWeb']
        ok_cnt = 0
        max_cnt = (4 if self.is_batch or 'Mac' != cst.PC else 6)

        try:
            # ブログランキング
            ok_cnt, err_msg, wdRank = self.pochiBrank(menu, ok_cnt, max_cnt, err_msg)

            # ブログ村
            ok_cnt, err_msg, wdMura = self.pochiBmura(menu, ok_cnt, max_cnt, err_msg)

            run_time = com.time_end(start_time)

            com.log(self.myjob + ': ' + ('正常終了' if 0 == len(err_msg) else '異常あり') +
                    '(' + com.conv_time_str(run_time) + ') [' + str(ok_cnt) + '/' + str(max_cnt) + ']',
                    ('' if 0 == len(err_msg) else 'W'))

            if not self.is_batch:
                if 0 == len(err_msg):
                    com.dialog(self.myjob + '\n正常終了しました。(' + com.conv_time_str(run_time) + ') [' +
                               str(max_cnt) + ']', '正常終了')
                else:
                    com.dialog(self.myjob + '\n途中でエラーがありました\n(' + com.conv_time_str(run_time) + ') [' +
                               str(ok_cnt) + '/' + str(max_cnt) + ']\n\n' + "\n".join(err_msg), 'エラー発生', 'W')

        finally:
            if self.is_batch:
                # try: wdRank.quit()
                # except: pass
                try: wdMura.quit()
                except: pass
        return

    # ブログランキング
    def pochiBrank(self, menu, ok_cnt, max_cnt, err_msg):
        wdRank = web_driver.driver(headless=self.is_batch)
        if wdRank is None:
            if not self.is_batch:
                com.dialog('WebDriver(ランキング)で異常が発生しました。', 'WebDriver異常', 'E')
            return
        try:
            wdRank.get(cst.BLOG_URL)
            wdRank.maximize_window()
            com.sleep(2)

            web_driver.find_element(wdRank, 'brank').click()
            com.sleep(1)
            ok_cnt += 1

            com.log('ランキング: IN (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
            com.sleep(2)

            brank = wdRank.window_handles[len(wdRank.window_handles) - 1]
            wdRank.switch_to.window(brank)

            is_err = False
            try:
                try:
                    web_driver.find_element(wdRank, 'jq-rfrank-link-rank-footer').click()
                    com.sleep(2)
                except: pass
                try:
                    web_driver.find_element(wdRank, 'jq-rfrank-link-close').click()
                    com.sleep(2)
                except: pass

                wdRank.get('https://blog.with2.net/out.php?id=1487139&url=https%3A%2F%2Fshock-nin.info')
                com.sleep(2)
                ok_cnt += 1

                com.log('ランキング: OUT (' + str(ok_cnt) + '/' + str(max_cnt) + ')')

                if 'Mac' != cst.PC:
                    wdRank.switch_to.window(wdRank.window_handles[len(wdRank.window_handles) - 1])
                    com.sleep(2)
                    wdRank.close()

            except:
                is_err = True
                err_msg.append('ランキング: OUT')
                com.log('ランキング: OUT失敗(' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')

            if not self.is_batch and 'Mac' == cst.PC:

                if not is_err:
                    wdRank.switch_to.window(brank)

                try:
                    wdRank.get('https://blog.with2.net/login')
                    com.sleep(5)

                    web_driver.find_element(wdRank, 'i-id').send_keys(menu['ブログランキング' == menu['SITE']]['ID1'].values[0])
                    web_driver.find_element(wdRank, 'i-pswd').send_keys(menu['ブログランキング' == menu['SITE']]['PASS'].values[0])
                    web_driver.find_element(wdRank, '/html/body/main/div/section/form/ul/li[4]/button').click()
                    com.sleep(1)

                    web_driver.find_element(wdRank, 'roulette-img').click()
                    ok_cnt += 1

                    com.log('ランキング: ルーレット (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
                except:
                    err_msg.append('ランキング: ルーレット')
                    com.log('ランキング: ルーレット失敗 (' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')

        except Exception as e:
            err_msg.append('予期せぬエラー: ブログランキング')
            com.log('エラー発生(' + str(ok_cnt) + '/' + str(max_cnt) + '): ' + str(e), 'E')

        return ok_cnt, err_msg, wdRank

    # ブログ村
    def pochiBmura(self, menu, ok_cnt, max_cnt, err_msg):
        wdMura = web_driver.driver(headless=self.is_batch)
        if wdMura is None:
            if not self.is_batch:
                com.dialog('WebDriver(ブログ村)で異常が発生しました。', 'WebDriver異常', 'E')
            return
        try:
            try:
                wdMura.get(cst.BLOG_URL)
                wdMura.maximize_window()
                com.sleep(2)

                web_driver.find_element(wdMura, 'bmura').click()
                ok_cnt += 1
                com.log('ブログ村: IN (' + str(ok_cnt) + '/' + str(max_cnt) + ')')

                wdMura.switch_to.window(wdMura.window_handles[len(wdMura.window_handles) - 1])

            except:
                err_msg.append('ブログ村: IN')
                com.log('ブログ村: IN失敗 (' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')

            try:
                com.sleep(2)
                wdMura.get('https://link.blogmura.com/out/?ch=' + menu['ブログ村' == menu['SITE']]['ID1'].values[0] +
                           '&url=https%3A%2F%2F' + cst.BLOG_URL.replace('https://', ''))
                # web_driver.find_element(wdMura2, title).click()
                ok_cnt += 1

                com.log('ブログ村: OUT (' + str(ok_cnt) + '/' + str(max_cnt) + ')')

            except Exception as e:
                err_msg.append('ブログ村: OUT')
                com.log('ブログ村: OUT失敗 (' + str(ok_cnt) + '/' + str(max_cnt) + '): ' + str(e), 'W')

            if 'Mac' == cst.PC:
                com.sleep(2)
                # wdMura.switch_to.window(wdMura.window_handles[len(wdMura.window_handles) - 1])
                # wdMura.close()

                wdMura.get('https://mypage.blogmura.com/login/')
                com.sleep(1)

                web_driver.find_element(wdMura, 'email').send_keys(menu['ブログ村' == menu['SITE']]['ID2'].values[0])
                web_driver.find_element(wdMura, 'password').send_keys(menu['ブログ村' == menu['SITE']]['PASS'].values[0])
                web_driver.find_element(wdMura, '/html/body/div/div/div[1]/form/div/input').click()

                com.log('ブログ村: ログイン')
                ok_cnt += 1

        except Exception as e:
            err_msg.append('予期せぬエラー: ブログ村')
            com.log('エラー発生(' + str(ok_cnt) + '/' + str(max_cnt) + '): ' + str(e), 'E')

        return ok_cnt, err_msg, wdMura
