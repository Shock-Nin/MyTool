#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst
from common import web_driver

import pyautogui as pgui
from selenium.webdriver.support.select import Select

class WebLogin:

    def __init__(self, job):
        self.myjob = job
        self.wd = web_driver.driver()

    def do(self, name, url):

        if self.wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return
        self.wd.get(url)

        pw_type = 'PwBank'
        menu = cst.MENU_CSV[pw_type][(cst.MENU_CSV[pw_type]['SITE'] == name)]
        if 0 == len(menu):
            pw_type = 'PwWeb'
            menu = cst.MENU_CSV[pw_type][(cst.MENU_CSV[pw_type]['SITE'] == name)]

        # クリック情報を取得
        id1, id2, pw, btn = _get_info(name)
        err_msg = ''
        
        # ログイン画面を開いて、
        if 0 < len(id1):
            com.sleep(1)
            try:
                # 事前画面あり
                if name in ['ガス']:
                    url += '/login.html'
                    self.wd.get(url)
                    com.sleep(1)

                # 特殊ログインパターン
                if 'ViewCard' == name:

                    for _ in range(0, 5):
                        try:
                            web_driver.find_element(self.wd, id1[1]).send_keys('')
                            web_driver.find_element(self.wd, id1[1]).send_keys(menu[id1[0]].values[0])
                            web_driver.find_element(self.wd, pw).send_keys('')
                            web_driver.find_element(self.wd, pw).send_keys(menu['PASS'].values[0])
                            web_driver.find_element(self.wd, btn).click()

                            com.sleep(1)
                            web_driver.find_element(self.wd, 'ImgV0300_001Header').click()
                            break
                        except:
                            com.sleep(1)
                            self.wd.get(url)

                    com.sleep(1)
                    web_driver.find_element(self.wd, 'LnkYotei').click()

                elif name in ['楽天カード']:

                    try:
                        web_driver.find_element(self.wd, id1[1]).send_keys('')
                        web_driver.find_element(self.wd, id1[1]).send_keys(menu[id1[0]].values[0])
                        web_driver.find_element(self.wd, 'cta001').click()
                        com.sleep(2)

                        web_driver.find_element(self.wd, pw).send_keys('')
                        web_driver.find_element(self.wd, pw).send_keys(menu['PASS'].values[0])
                        web_driver.find_element(self.wd, 'cta011').click()

                        # web_driver.find_element(self.wd, 'loginInner_birthday').send_keys('')
                        # web_driver.find_element(self.wd, 'loginInner_birthday').send_keys(menu['19800226'].values[0])

                        com.sleep(2)
                    except:
                        pass

                elif name in ['PayPayカード']:

                    try:
                        web_driver.find_element(self.wd, id1[1]).send_keys('')
                        web_driver.find_element(self.wd, id1[1]).send_keys(menu[id1[0]].values[0])
                        web_driver.find_element(self.wd, '//*[@id="content"]/div[1]/div/form/div[1]/div[1]/div[2]/div/button').click()
                        com.sleep(2)

                        # web_driver.find_element(self.wd, pw).send_keys('')
                        # web_driver.find_element(self.wd, pw).send_keys(menu['PASS'].values[0])
                        # web_driver.find_element(self.wd, 'cta011').click()

                        com.sleep(2)
                    except:
                        pass

                else:
                    if '三菱UFJ' == name:
                        com.sleep(3)
                        web_driver.find_element(self.wd, 'tx-branch-number').send_keys('')
                    elif '三井住友' == name:
                        web_driver.find_element(self.wd, 'tab-switchB02').click()

                    web_driver.find_element(self.wd, id1[1]).send_keys('')
                    web_driver.find_element(self.wd, id1[1]).send_keys(menu[id1[0]].values[0])

                    if name in ['三井住友', 'e-Staffing']:
                        web_driver.find_element(self.wd, id1[1]).send_keys('')
                        web_driver.find_element(self.wd, id2[1]).send_keys(menu[id2[0]].values[0])

                    web_driver.find_element(self.wd, pw).send_keys('')
                    web_driver.find_element(self.wd, pw).send_keys(menu['PASS'].values[0])

                    if '三井住友' == name:
                        for i in range(3, 5):
                            try:
                                web_driver.find_element(self.wd, btn + '[' + str(i) + ']/a').click()
                            except: pass
                        try:
                            web_driver.find_element(self.wd, 'pwChangeStopFlag').click()
                            web_driver.find_element(self.wd, '//*[@id="main-area"]/div/section/div[2]/a').click()
                        except: pass
                        com.sleep(7)
                        try:
                            web_driver.find_element(self.wd, '//*[@id="TPALTOPtop"]/div[2]/div[3]/div/div[2]/div/div/i').click()
                        except: pass

                    elif 0 < len(btn):
                        web_driver.find_element(self.wd, btn).click()

                    if '三菱UFJ' == name:
                        if 'お知らせ - 三菱ＵＦＪ銀行' == self.wd.title:
                            try:
                                web_driver.find_element(
                                    self.wd, '//*[@id="contents"]/div[2]/div[1]/table/tbody/tr/td[5]/form/input[4]').click()
                                com.sleep(1)
                                web_driver.find_element(self.wd, '次の明細を表示').click()
                            except:
                                web_driver.find_element(self.wd, 'top').click()

                    if 'JREBANK' == name:

                        try:
                            com.sleep(1)
                            account = menu['ID2'].values[0].split('_')
                            select = web_driver.find_element(self.wd, 'j_id_1h:INPUT_BRANCH_CODE')

                            options = Select(select).options
                            num = -1
                            for k in range(len(options)):
                                if options[k].text.endswith(account[0]):
                                    num = k
                                    break
                            Select(select).select_by_index(num)

                            elm = '//*[@id="j_id_1h"]/section[2]/div[1]/div/fieldset[2]/label/input'
                            web_driver.find_element(self.wd, elm).send_keys('')
                            web_driver.find_element(self.wd, elm).send_keys(account[1])

                            elm = '//*[@id="j_id_1h"]/section[2]/div[2]/div/fieldset[1]/input'
                            web_driver.find_element(self.wd, elm).send_keys('')
                            web_driver.find_element(self.wd, elm).send_keys('ああああ')

                            com.sleep(1)
                            web_driver.find_element(self.wd, 'j_id_7d').click()
                        except:
                            pass

                # 事後画面あり
                if name in ['楽天銀行', '岡三総合', 'リクルート']:
                    com.sleep(1)

                    if '楽天銀行' == name:
                        try:
                            pgui.hotkey('eisu')
                            pgui.write('225')
                            pgui.hotkey('tab')
                            pgui.write('2152671')
                            pgui.hotkey('tab')
                            pgui.hotkey('tab')
                            com.clip_copy('ああああ')
                            web_driver.find_element(self.wd, 'INPUT_FORM:j_id_28').click()
                            com.sleep(1)
                        except: pass
                        try:
                            web_driver.find_element(self.wd, 'INPUT_FORM_P:_idJsp176').click()
                        except: pass

                    elif name in ['リクルート']:
                        self.wd.get('https://www.r-staffing.co.jp/sol/op65/sd01/')

                    else:
                        url = ('buttonOK' if '岡三総合' == name else '')
                        web_driver.find_element(self.wd, url).click()

            except Exception as e:
                err_msg = str(e)

        com.log('ログイン' + ('エラー' if 0 < len(err_msg) else '') + ': ' + name + ', ' + url)
        if 0 < len(err_msg):
            com.log(err_msg)
            com.dialog(err_msg, 'ログインエラー', 'E')

        com.sleep(1)
        return self.wd


def _get_info(name):
    info = [], [], '', ''

    # 資産
    if 'ViewCard' == name:
        info = ['ID1', 'id'], ['', ''], 'pass', '//input[@alt=\'ログイン\']'
    elif '楽天カード' == name:
        info = ['ID1', 'user_id'], ['', ''], 'password_current', ''
    elif 'PayPayカード' == name:
        info = ['ID1', 'login_handle'], ['', ''], 'password_current', ''
    elif '三井住友' == name:
        info = ['ID1', 'userId1'], ['ID2', 'userId2'], 'password', '//*[@id="main-area"]/div/section/div'
    elif '三菱UFJ' == name:
        info = ['ID1', 'tx-contract-number'], ['', ''], 'tx-ib-password', 'button.gonext'
    elif '楽天銀行' == name:
        info = ['ID1', 'LOGIN:USER_ID'], ['', ''], 'LOGIN:LOGIN_PASSWORD', '//*[@id="LOGIN"]/div[7]/a'
    elif 'JREBANK' == name:
        info = ['ID1', '//*[@id="j_id_t"]/div[1]/div[2]/fieldset/p[1]/input'], ['', ''], 'j_id_t:LOGIN_PASSWORD', 'j_id_22'
    # 生活
    elif '水道' == name:
        info = ['ID1', 'userName'], ['', ''], 'password', '//*[@id="loginForm"]/table/tbody/tr[4]/td/input'
    elif 'ガス' == name:
        info = ['ID1', 'loginId'], ['', ''], 'password', 'submit-btn'
    # 投資
    elif '岡三総合' == name:
        info = ['ID1', 'loginTuskLoginId'], ['', ''], 'gnziLoginPswd', 'buttonLogin'
    elif '岡三365' == name:
        info = ['ID1', 'loginId'], ['', ''], 'password', '//*[@id="loginBtn"]/input'
    elif 'FxPro' == name:
        info = ['ID2', 'input-email'], ['', ''], 'login-input-password', 'login-signin-button'
    elif 'MyFx' == name:
        info = ['ID2', 'email'], ['', ''], 'tradingDeskPassword', '//*[@id="loginForm"]/div[2]/button'
    elif 'GogoJungle' == name:
        info = ['ID1', 'email'], ['', ''], 'password', \
               '//*[@id="__layout"]/div/main/div[2]/div/div[1]/div[1]/button'
    # 派遣
    elif 'リクルート' == name:
        info = ['ID1', 'user_id'], ['', ''], 'user_pass', \
               '//*[@id="backgroundcolor"]/div[1]/div/div/div[1]/div/form/div[4]/div[2]/div/a/span/span'
    elif 'パーソル' == name:
        info = ['ID1', 'mprnUserId'], ['', ''], 'mprnPass', 'btnLogin'
    elif 'パソナ' == name:
        info = ['ID1', 'username'], ['', ''], 'password', 'kc-login'
    elif 'e-Staffing' == name:
        info = ['ID2', 'compid'], ['ID1', 'userid'], 'pwd', 'Image1'
    # ASP
    elif 'キャッシュバック' == name:
        info = ['ID1', 'UserEmail'], ['', ''], 'UserPassword', '//*[@id="UserLoginForm"]/div[3]/div/button'
    elif '口座開設' == name:
        info = ['ID1', 'mail'], ['', ''], 'passwd', '//*[@id="inc_side_body"]/div[2]/dl/dd[1]/form/div/input'

    return info
