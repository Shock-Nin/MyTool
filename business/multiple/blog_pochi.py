#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst
from common import web_driver


class BlogPochi:

    def __init__(self, job):
        self.myjob = job
        self.is_batch = ('Batch' == job)
        self.wd = web_driver.driver()

    def do(self):

        if self.wd is None:
            if not self.is_batch:
                com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return

        start_time = com.time_start()
        com.log('ブログクリック開始')
        err_msg = []

        menu = cst.MENU_CSV['PwWeb']
        ok_cnt = 0
        max_cnt = (4 if self.is_batch or 'Mac' != cst.PC else 5)

        try:
            self.wd.get(cst.BLOG_URL)
            self.wd.maximize_window()
            home = self.wd.window_handles[0]

            # ブログランキング
            blog_title = self.wd.title
            web_driver.find_element(self.wd, 'brank').click()
            ok_cnt += 1

            com.log('ランキング: IN (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
            com.sleep(2)

            brank = self.wd.window_handles[len(self.wd.window_handles) - 1]
            self.wd.switch_to.window(brank)

            is_err = False
            try:
                try:
                    web_driver.find_element(self.wd, 'jq-rfrank-link-rank-footer').click()
                    com.sleep(1)
                except: pass
                try:
                    web_driver.find_element(self.wd, 'jq-rfrank-link-close').click()
                    com.sleep(1)
                except: pass

                if 'Mac' == cst.PC:
                    web_driver.find_element(self.wd, blog_title).click()
                else:
                    self.wd.get('https://blog.with2.net/out.php?id=1487139&url=https%3A%2F%2F' +
                                cst.BLOG_URL.replace('https://', ''))
                ok_cnt += 1

                com.log('ランキング: OUT (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
                com.sleep(1)

                self.wd.switch_to.window(self.wd.window_handles[len(self.wd.window_handles) - 1])
                com.sleep(2)
                self.wd.close()

            except:
                is_err = True
                err_msg.append('ランキング: OUT')
                com.log('ランキング: OUT失敗(' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')

            if not self.is_batch and 'Mac' == cst.PC:

                if not is_err:
                    self.wd.switch_to.window(brank)

                try:
                    self.wd.get('https://blog.with2.net/login')
                    com.sleep(2)

                    web_driver.find_element(self.wd, 'i-id').send_keys(menu['ブログランキング' == menu['SITE']]['ID1'].values[0])
                    web_driver.find_element(self.wd, 'i-pswd').send_keys(menu['ブログランキング' == menu['SITE']]['PASS'].values[0])
                    web_driver.find_element(self.wd, '/html/body/main/div/section/form/ul/li[4]/button').click()
                    com.sleep(1)

                    web_driver.find_element(self.wd, 'roulette-img').click()
                    ok_cnt += 1

                    com.log('ランキング: ルーレット (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
                except:
                    err_msg.append('ランキング: ルーレット')
                    com.log('ランキング: ルーレット失敗 (' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')
            try:
                self.wd.switch_to.window(home)
                com.sleep(1)

                # ブログ村
                web_driver.find_element(self.wd, 'bmura').click()
                ok_cnt += 1

                com.log('ブログ村: IN (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
                com.sleep(1)

                bmura = self.wd.window_handles[len(self.wd.window_handles) - 1]
                self.wd.switch_to.window(bmura)

            except:
                err_msg.append('ブログ村: IN')
                com.log('ブログ村: IN失敗 (' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')
            try:
                web_driver.find_element(self.wd, '/html/body/div[5]/div[1]/div/div/a').click()
                ok_cnt += 1

                com.log('ブログ村: OUT (' + str(ok_cnt) + '/' + str(max_cnt) + ')')
                com.sleep(1)

            except:
                err_msg.append('ブログ村: OUT')
                com.log('ブログ村: OUT失敗 (' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'W')

            if 'Mac' == cst.PC:

                self.wd.switch_to.window(self.wd.window_handles[len(self.wd.window_handles) - 1])
                com.sleep(2)
                self.wd.close()

                self.wd.switch_to.window(bmura)
                self.wd.get('https://mypage.blogmura.com/login/')
                com.sleep(1)

                web_driver.find_element(self.wd, 'email').send_keys(menu['ブログ村' == menu['SITE']]['ID1'].values[0])
                web_driver.find_element(self.wd, 'password').send_keys(menu['ブログ村' == menu['SITE']]['PASS'].values[0])
                web_driver.find_element(self.wd, '/html/body/div/div/div[1]/form/div/input').click()

                com.log('ブログ村: ログイン')
                self.wd.switch_to.window(brank)
            else:
                self.wd.switch_to.window(bmura)

        except Exception as e:
            com.log('エラー発生(' + str(ok_cnt) + '/' + str(max_cnt) + '): ' + str(e), 'E')
        finally:
            if self.is_batch:
                try:
                    self.wd.close()
                    self.wd.quit()
                except: pass

        run_time = com.time_end(start_time)

        com.log(self.myjob + ': ' + ('正常終了' if ok_cnt == max_cnt else '異常あり') +
                '(' + com.conv_time_str(run_time) + ') [' + str(ok_cnt) + '/' + str(max_cnt) + ']',
                ('' if ok_cnt == max_cnt else 'W'))

        if not self.is_batch:
            if ok_cnt == max_cnt:
                com.dialog(self.myjob + '\n正常終了しました。(' + com.conv_time_str(run_time) + ') [' +
                           str(max_cnt) + ']', '正常終了')
            else:
                com.dialog(self.myjob + '\n途中でエラーがありました\n(' + com.conv_time_str(run_time) + ') [' +
                           str(ok_cnt) + '/' + str(max_cnt) + ']\n\n' + "\n".join(err_msg), 'エラー発生', 'W')

        return self.wd
