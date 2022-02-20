#!/usr/bin/env python
# -*- coding: utf-8 -*-

from const import cst

import os
import logging
import inspect
import datetime
import smtplib
import pandas as pd
from email.mime.text import MIMEText

# スリープ直接呼び出し
from time import sleep

# display
from common import display
dialog = display.dialog
question = display.question
dialog_cols = display.dialog_cols
progress = display.progress
close = display.close

# matching
from common import matching
move_pos = matching.move_pos
click_pos = matching.click_pos
match = matching.match


# 日時を文字型で取得
def str_time(ymd=True):
    return datetime.datetime.now().strftime(('%Y-%m-%d ' if ymd else '') + '%H:%M:%S')


# 実行メソッドの取得
def get_method(before=0):
    stack = inspect.stack()[before + 2]
    file = stack.filename.replace(os.getcwd(), '')
    return file[1: file.rfind('.')] + '/' + stack.function


# ログをレベルに応じて出力
def log(msg, lv=''):
    logger = _format()
    msg = ' ' + get_method() + ' | ' + msg

    if 'E' == lv:
        logger.error(msg)

        # エラー時は専用メールで送受信
        send_mail('エラー発生[ ' + cst.IPS[cst.IP] + ' | ' + cst.IP + ' ]', msg,
                  cst.ERROR_MAIL, cst.ERROR_MAIL, cst.ERROR_MAIL_PW)

    elif 'W' == lv:
        logger.warning(msg)
    else:
        logger.info(msg)


# ログフォーマット
def _format():
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s]%(message)s', level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(
            cst.TEMP_PATH[cst.PC] + 'Log/' +
            datetime.datetime.now().strftime('%Y-%m-%d').replace('-', '').split(' ')[0] + '.log')])
    return logger


# ログフォルダ作成
if not os.path.exists(cst.TEMP_PATH[cst.PC]):
    os.mkdir(cst.TEMP_PATH[cst.PC])
if not os.path.exists(cst.TEMP_PATH[cst.PC] + 'Log'):
    os.mkdir(cst.TEMP_PATH[cst.PC] + 'Log')

# ログファイル削除
files = os.listdir(cst.TEMP_PATH[cst.PC] + 'Log')
files.sort()
for i in range(0, len(files) - cst.KEEP_LOG):
    os.remove(cst.TEMP_PATH[cst.PC] + 'Log/' + files[i])
    log('ログ削除: ' + files[i])


# メール送信(デフォルトアカウントはブログ)
def send_mail(subject, body, to, account=cst.BLOG_MAIL, password=cst.BLOG_MAIL_PW):

    # MIMETextを作成
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['To'] = to
    msg['From'] = account

    # サーバを指定する
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(account, password)

    # メールを送信する
    server.send_message(msg)

    # 閉じる
    server.quit()

    log('メール送信: [' + to + '] ' + subject + ' : ' + body)


# メニュー系CSV読み込み
def get_menu():
    path = cst.GDRIVE_PATH[cst.PC] + 'menu/'
    err_msg = ''
    try:
        for file in cst.MENU_CSV:
            cst.MENU_CSV[file] = pd.read_csv(path + file + '.csv', encoding='cp932')

    except Exception as e:
        log('読み込みエラー: ' + path + file + ' |' + str(e))
        err_msg += '\n　' + path + file

    if 0 < len(err_msg):
        dialog('読み込みエラー\n' + err_msg, '読み込みエラー', 'E')
        return False

    return True
