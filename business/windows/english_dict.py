#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

from common import web_driver

import os
import pandas as pd
import PySimpleGUI as sg
import urllib.parse

FUNCTIONS = [
    ['基本マスタ', '_create_master'],
    ['コンテンツ', '_get_contents'],
    ['イメージ', '_get_images']
]

class EnglishDict:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        selects = com.dialog_cols('不要なものは外してください。',
                                  [[FUNCTIONS[i][0] for i in range(0, len(FUNCTIONS))]],
                                  ['l' for _ in range(0, len(FUNCTIONS))], '工程選択', obj='check')
        if 0 == len(selects):
            return

        total_time = 0

        for i in range(0, len(FUNCTIONS)):

            if FUNCTIONS[i][0] not in selects[0]:
                continue

            start_time = com.time_start()
            is_run = getattr(self, FUNCTIONS[i][1])()

            if is_run is None:
                com.dialog('中断しました。', self.myjob)
                return
            elif not is_run:
                return

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log(FUNCTIONS[i][0] + ': 完了(' + com.conv_time_str(run_time) + ')')

        com.log(self.myjob + ': 全終了(' + com.conv_time_str(total_time) + ')')
        com.dialog('完了しました。(' + com.conv_time_str(total_time) + ')', self.myjob)

    def _create_master(self):

        wd = web_driver.driver()
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        data = {}
        try:
            # 4段階のレベル単位で、約2000語のループ
            for lv in range(1, cst.ENGLISH_MASTER_LEVEL + 1):

                index = 1
                words = []
                total_time = 0

                window = com.progress(self.myjob, ['lv', cst.ENGLISH_MASTER_LEVEL], interrupt=True)
                event, values = window.read(timeout=0)

                while True:

                    start_time = com.time_start()

                    # 50語単位リストページのHTML取得を10回まで実施
                    is_html = False
                    for i in range(0, 10):

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        window['lv'].update('Lv ' + str(lv) + '/' + str(cst.ENGLISH_MASTER_LEVEL) +
                                            ' - ' + str(index) + ' :' + str(i + 1))
                        window['lv_'].update(lv - 1)

                        wd.get(cst.ENGLISH_MASTER_URL + str(lv) + '/' + str(index))
                        com.sleep(3)
                        try:
                            html = wd.page_source
                            is_html = True
                            break
                        except: pass

                    if not is_html:
                        com.log('HTML取得ミス: Lv' + str(lv) + ' - ' + str(index), lv='W')
                        com.dialog('HTMLを取得ミスしました。\n　Lv' + str(lv) + ' - ' + str(index),
                                   title='TML取得ミス', lv='W')
                        return False

                    html = html[html.find('を表示しています'): html.find('掲載しています。')]
                    html = html[html.find('</table'): html.rfind('<div')]
                    html = html[html.find('</tr'): html.rfind('<td ')]

                    # 全体でimgタグがない場合は不在ページ、ループを抜けて次レベルへ
                    if html.find('<img') < 0:
                        break

                    html = html[html.find('<tr>') + 4:].replace('\n', '').split('<hr>')

                    for row in html:
                        # imgタグがなくなったら、ループを抜けて次50語リストへ
                        if row.find('<img') < 0:
                            break

                        row = row[row.find('<a '): row.rfind('</tr>')]
                        row = row[row.find('>') + 1: row.rfind('</td>')]

                        word = row[: row.find('</a>')]
                        img = row[row.find('<img '): row.find('.gif')]
                        img = img[img.rfind('/') + 1:]
                        jpn = row[row.rfind('>') + 1:]

                        words.append(str(lv) + ',' + word + ',' + img + ',' + jpn)

                    # 中断イベント
                    if _is_interrupt(window, event):
                        return None

                    run_time = com.time_end(start_time)
                    total_time += run_time

                    com.log('Master(' + com.conv_time_str(run_time) + '): Lv' + str(lv) + ' - ' +
                            str(index) + ' (' + str(len(words)) + ')')
                    index += 1

                com.log('Master(' + com.conv_time_str(total_time) + '): Lv' + str(lv))
                data[lv] = words
                window.close()

            with open(cst.TEMP_PATH[cst.PC] + 'English/Master.csv', 'w', encoding='utf8') as outfile:
                [[outfile.write(row + '\n') for row in data[lv]] for lv in data]

        except Exception as e:
            com.log(self.myjob + ' エラー発生: ' + str(e), lv='W')
            com.dialog(self.myjob + ' でエラーが発生しました。\n' + str(e), title='エラー発生', lv='W')
            return False

        finally:
            try: window.close()
            except: pass
            try: wd.quit()
            except: pass

        return True

    def _get_contents(self):

        wd = web_driver.driver()
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        try:
            with open(cst.TEMP_PATH[cst.PC] + 'English/Master.csv', 'r') as read_file:
                words = {}

                for row in read_file.read().split('\n'):
                    cols = row.split(',')

                    total_time = 0

                    window = com.progress(self.myjob, ['lv', len(read_file.read().split('\n'))], interrupt=True)
                    event, values = window.read(timeout=0)

                    # 50語単位リストページのHTML取得を10回まで実施
                    is_html = False
                    for i in range(0, 10):

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        window['lv'].update('Lv ' + str(lv) + '/' + str(cst.ENGLISH_MASTER_LEVEL) +
                                            ' - ' + str(index) + ' :' + str(i + 1))
                        window['lv_'].update(lv - 1)

                        wd.get(cst.ENGLISH_CONTENTS_URL % cols[1])
                        com.sleep(2)

                        try:
                            html = wd.page_source
                            is_html = True
                            break
                        except: pass

                    if not is_html:
                        com.log('HTML取得ミス: Lv' + str(lv) + ' - ' + str(index), lv='W')
                        com.dialog('HTMLを取得ミスしました。\n　Lv' + str(lv) + ' - ' + str(index),
                                   title='TML取得ミス', lv='W')
                        return False


                    html = html[html.find('発音記号・読み方'): html.find('例文の一覧を見る')].replace('\n', '')

                    pronounce = html[html.find('phoneticEjjeDesc'):]
                    pronounce = pronounce[:pronounce.find('</span>')]
                    pronounce = pronounce[pronounce.find('>'):]

                    change_col = html[html.find('変形一覧'): html.find('学習レベル')]
                    change_col = change_col[change_col.find('<table'): change_col.rfind('</table>')]
                    change_col = change_col[change_col.find('<span>') + 6: change_col.rfind('</span>')].split('</span>')

                    changes = []
                    txt = []
                    # for col in change_col:
                    #     col =
                    #     txt.append()



                    example_col = html[html.find('を含む例文一覧') + 10:]
                    example_col = example_col[example_col.find('<a '): example_col.rfind('<span>')]
                    example_col = example_col[example_col.find('>'):]
                    print(pronounce)
                    print(change_col)
                    print(example_col)
                    print('-------')

                    examples = []

                    noun = {'doushi': '動詞', 'meishi': '名刺', 'keiyoshi': '形容詞', 'fukushi': '副詞', 'zenchishi': '前置詞'}[cols[2]]

                    words[cols[1]] = [{'pronounce': pronounce}, {'changes': [noun] + changes},
                                      {'japanese': cols[3]}, {'examples': examples}]

        finally:
            pass
            # try: wd.quit()
            # except: pass

        return True

    def _get_images(self):

        wd = web_driver.driver()
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        try:
            wd.get(urllib.parse.quote(cst.ENGLISH_IMAGES_URL, 'utf8'))
            com.sleep(5)
        finally:
            pass
            # try: wd.quit()
            # except: pass


        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
