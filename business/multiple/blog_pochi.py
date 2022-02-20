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

        com.log('ブログクリック開始')
        menu = cst.MENU_CSV['PwWeb']
        ok_cnt = 0
        max_cnt = (4 if self.is_batch else 5)

        try:
            self.wd.get(cst.BLOG_URL)
            self.wd.maximize_window()
            home = self.wd.window_handles[0]

            # ブログランキング
            blog_title = self.wd.title
            web_driver.find_element(self.wd, 'brank').click()
            ok_cnt += 1

            com.log('ランキング: IN ' + str(ok_cnt) + '/' + str(max_cnt))
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

                web_driver.find_element(self.wd, blog_title).click()
                ok_cnt += 1

                com.log('ランキング: OUT ' + str(ok_cnt) + '/' + str(max_cnt))
                com.sleep(1)

                self.wd.switch_to.window(self.wd.window_handles[len(self.wd.window_handles) - 1])
                com.sleep(2)
                self.wd.close()

            except:
                is_err = True
                com.log('ランキング: OUT失敗', 'W')

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

                    com.log('ルーレット: ' + str(ok_cnt) + '/' + str(max_cnt))
                except:
                    com.log('ルーレット: 失敗', 'W')
            try:
                self.wd.switch_to.window(home)
                com.sleep(1)

                # ブログ村
                web_driver.find_element(self.wd, 'bmura').click()
                ok_cnt += 1

                com.log('ブログ村: IN ' + str(ok_cnt) + '/' + str(max_cnt))
                com.sleep(1)

                bmura = self.wd.window_handles[len(self.wd.window_handles) - 1]
                self.wd.switch_to.window(bmura)

            except:
                com.log('ブログ村: IN失敗', 'W')
            try:
                web_driver.find_element(self.wd, '/html/body/div[5]/div[1]/div/div/a').click()
                ok_cnt += 1

                com.log('ブログ村: OUT ' + str(ok_cnt) + '/' + str(max_cnt))
                com.sleep(1)

            except:
                com.log('ブログ村: OUT失敗', 'W')

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

        com.log(('正常終了' if ok_cnt == max_cnt else '異常あり') + ': ' + str(ok_cnt) + '/' + str(max_cnt),
                ('' if ok_cnt == max_cnt else 'W'))

        if not self.is_batch and ok_cnt != max_cnt:
            com.dialog('途中でエラーがありました。(' + str(ok_cnt) + '/' + str(max_cnt) + ')', 'エラー発生', 'W')

        return self.wd
