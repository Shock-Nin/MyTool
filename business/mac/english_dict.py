#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from const import cst

from common import web_driver
from common import com

import re
import json
import pykakasi
import pandas as pd
import PySimpleGUI as sg
import pyautogui as pgui
import urllib.request
import pyperclip

from selenium.webdriver.common.keys import Keys

IS_HEADLESS = True

FUNCTIONS = [
    ['基本マスタ', '_create_master', 'Master', 'csv'],
    ['Weblio', '_get_weblio', 'Weblio', 'json'],
    ['英ナビ', '_get_Einavi', 'Einavi', 'json'],
    ['Google', '_get_google', 'Google', 'json'],
    ['MP3取得', '_get_mp3', 'Content', 'js'],
    ['辞書', '_merge_content', 'Content', 'json'],
    ['フレーズ集', '_create_phrases', 'Phrase', 'csv'],
]
OTHER_START = 5
PHRASE_SUFFIX = ['able', 'ful', 'ness', 'less', 'ress', 'lity', 'rity', 'ment']
IGNORE_MEANINGS = ['関係代名詞', '現在完了', '過去完了', '未来完了']
MP3_PATH = cst.TEMP_PATH[cst.PC] + 'English/mp3'
MP3_DL = [['Weblio', 0], ['LONGMAN', 0], ['英ナビ', 0], ['音読', 12]]

class EnglishDict:

    def __init__(self, job):
        self.myjob = job

    def do(self):
        layout = [[FUNCTIONS[i][0] + '_' + str(k)
                   for k in range(1, int(cst.ENGLISH_MASTER_LEVEL / (2 if i in [4] else 1)) + 1)] +
                  [FUNCTIONS[i][0] + '_追加' if i in [1, 2, 3] else
                   FUNCTIONS[i][0] + '_マージ' if i in [0] else None]
                  for i in range(0, len(FUNCTIONS) - 2)]
        layout.append([FUNCTIONS[i][0] for i in range(5, len(FUNCTIONS))])

        selects = com.dialog_cols('不要なものは外してください。', layout,
                                  ['l' for _ in range(0, len(FUNCTIONS))], '工程選択', obj='check')
        if 0 == len(selects):
            return
        total_time = 0

        others = selects[len(selects) - 1].copy()
        selects[len(selects) - 1] = []

        for i in range(OTHER_START, len(FUNCTIONS)):
            if FUNCTIONS[i][0] in others:

                if OTHER_START == i:
                    selects[len(selects) - 1] = [others[0]]
                else:
                    selects.append([FUNCTIONS[i][0]])
            elif OTHER_START != i:
                selects.append([])

        for i in range(0, len(FUNCTIONS)):
            if 0 == len(selects[i]):
                continue

            start_time = com.time_start()
            is_run = getattr(self, FUNCTIONS[i][1])(selects[i])

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

    # マスタ取得
    def _create_master(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd_error = 0
        is_merge = False

        try:
            # 4段階のレベル単位で、約2000語のループ
            for select in selects:

                if 0 <= select.find('マージ'):
                    is_merge = True
                    continue

                lv = int(select.split('_')[1])

                data = {}
                words = []
                total_time = 0

                window = com.progress(self.myjob, ['lv', cst.ENGLISH_MASTER_LEVEL], interrupt=True)
                event, values = window.read(timeout=0)

                while True:

                    start_time = com.time_start()

                    # 50語単位リストページのHTML取得を、1分まで実施
                    is_html = False
                    for i in range(0, 60):

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        window['lv'].update('Lv ' + str(lv) + '/' + str(cst.ENGLISH_MASTER_LEVEL) +
                                            ' [' + str(i + 1) + ', wd' + str(wd_error) + ']')
                        window['lv_'].update(lv - 1)

                        try:
                            wd.get(cst.ENGLISH_MASTER_URL % (('' if 10 <= lv else '0') + str(lv)))
                            html = wd.page_source
                            html = html[html.find('<font') + 1:]
                            is_html = True
                            break
                        except:
                            wd_error += 1
                            try: wd.quit()
                            except: pass
                            try: wd = web_driver.driver(headless=IS_HEADLESS)
                            except: pass
                            com.sleep(1)

                    if not is_html:
                        com.log('HTML取得ミス: Lv' + str(lv), lv='W')
                        com.dialog('HTMLを取得ミスしました。\n　Lv' + str(lv),
                                   title='TML取得ミス', lv='W')
                        return False

                    html = html[html.find('<font'):]
                    html = html[html.find('>') + 1: html.find('</font>')].split('<br>')

                    for row in html:
                        if 0 < len(row):
                            words.append(str(lv) + ',' + row.strip())

                    # 中断イベント
                    if _is_interrupt(window, event):
                        return None

                    run_time = com.time_end(start_time)
                    total_time += run_time

                    com.log('Master(' + com.conv_time_str(run_time) + '): Lv' + str(lv) + '(' + str(len(words)) + ')')
                    break

                com.log('Master(' + com.conv_time_str(total_time) + '): Lv' + str(lv))
                data[lv] = words
                window.close()

                with open(cst.TEMP_PATH[cst.PC] + 'English/Master_' + str(lv) + '.csv', 'w',
                          encoding='utf8') as outfile:
                    [[outfile.write(row + '\n') for row in data[lv]] for lv in data]

        except Exception as e:
            com.log(self.myjob + ' マスタ作成 エラー発生: ' + str(e), lv='W')
            com.dialog(self.myjob + ' マスタ作成 でエラーが発生しました。\n' + str(e), title='エラー発生', lv='W')
            return False

        finally:
            try: window.close()
            except: pass
            try: wd.quit()
            except: pass

        # マージを実行する場合
        if is_merge:
            self._merge_master(0)

        return True

    # Master.csv作成
    def _merge_master(self, fnc):

        merge_file = cst.TEMP_PATH[cst.PC] + 'English/' + FUNCTIONS[fnc][2] + '.' + FUNCTIONS[fnc][3]
        datas = []

        for lv in range(1, cst.ENGLISH_MASTER_LEVEL + 1):
            data = pd.read_csv(merge_file.replace(
                FUNCTIONS[fnc][2] + '.', FUNCTIONS[fnc][2] + '_' + str(lv) + '.'), header=None)

            rows = []
            for i in range(0, len(data)):
                phrase = data.at[i, 1]

                for txt in [phrase]:
                    rows.append(txt)

            datas.append(pd.DataFrame(data=[[str(lv), row] for row in rows]))

        datas = pd.concat(datas)
        datas = datas.drop_duplicates(datas.columns[[1]]).copy()

        datas.to_csv(merge_file, header=False, index=False)
        return True

    # Weblio取得
    def _get_weblio(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd_error = 0
        insert = '追加' == selects[0].split('_')[1]

        try:
            datas = open(cst.TEMP_PATH[cst.PC] + 'English/' +
                         ('Weblio' if insert else 'Master') + '.csv', 'r').read().split('\n')
            if insert:
                selects = ['追加_' + str(k) for k in range(1, cst.ENGLISH_MASTER_LEVEL + 1)]
            insert_datas = []

            for select in selects:

                lv = int(select.split('_')[1])
                rows = [row for row in datas if str(lv) == row.split(',')[0]]

                words = []
                total_times = 0
                count = 0

                window = com.progress(self.myjob, ['lv', cst.ENGLISH_MASTER_LEVEL],
                                      ['target', len(rows)], interrupt=True)
                event, values = window.read(timeout=0)

                for row in rows:

                    word = {}
                    cols = row.split(',')
                    targets = cols[1].split('-' if 0 <= cols[1].find('-') else ' ')
                    start_time = com.time_start()

                    # 単語個別のHTML取得を、1分まで実施
                    for target in targets:

                        is_html = False
                        for i in range(0, 60):

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return None

                            window['lv'].update(('追加: ' if insert else '') + 'Lv ' + str(lv) + '/' +
                                                str(cst.ENGLISH_MASTER_LEVEL) + ' [' + str(i + 1) +
                                                ', wd' + str(wd_error) + ']')
                            window['lv_'].update(lv - 1)
                            window['target'].update(target + ' ' + str(count + 1) + '/' + str(len(rows)))
                            window['target_'].update(count)

                            try:
                                wd.get(cst.ENGLISH_DICT_URL['Weblio'][0] % target)
                                html = wd.page_source
                                html = html[html.find('意味・対訳'): html.find('例文の一覧を見る')].replace('\n', '')
                                is_html = True
                                break
                            except:
                                wd_error += 1
                                try: wd.quit()
                                except: pass
                                try: wd = web_driver.driver(headless=IS_HEADLESS)
                                except: pass
                                com.sleep(1)

                        if not is_html:
                            com.log('HTML取得ミス: Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target, lv='W')
                            com.dialog('HTMLを取得ミスしました。\n　Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target,
                                       title='HTML取得ミス', lv='W')
                            return False

                        # 発音表記
                        if 0 <= html.find('phoneticEjjeDesc'):
                            pronounce = html[html.find('phoneticEjjeDesc'):]
                        else:
                            pronounce = html[html.find('syllableEjje'):]

                        pronounce = pronounce[:pronounce.find('</div>')]
                        pronounce = pronounce[pronounce.find('>') + 1: pronounce.rfind('</span>')]
                        pronounce = pronounce.replace('<span class="phoneticEjjeDc">', ''). \
                            replace('<span class="phoneticEjjeDesc">', ''). \
                            replace('<span class="phoneticEjjeExt">', '').replace('</span>', '')
                        pronounce = pronounce[:pronounce.rfind(')') + 1]

                        # 意味・対訳
                        meaning = html[html.find('>') + 1: html.find('</div>')]
                        meaning = meaning[: meaning.rfind('</span>')]
                        meaning = meaning[meaning.rfind('>') + 1:].replace('(通例', '(').replace('通例 ', '').strip()

                        # 品詞
                        partspeech_col = html[html.find('品詞ごとの'):]
                        partspeech_col = partspeech_col[: html.find('イディオムやフレーズ')]
                        partspeech_col = partspeech_col[partspeech_col.find('<div '): partspeech_col.find('</div>')]
                        partspeech_col = partspeech_col[partspeech_col.find('>') + 2: -1].split('><')

                        partspeech = []
                        for col in partspeech_col:
                            if col.find('語源') < 0:
                                col = col[col.find('>') + 1: col.rfind('としての')]
                                col = col.replace('【', '').replace('】', '')
                                col = (col.replace(' ', '(') + ')' if 0 <= col.find(' ') else col)
                                partspeech.append(col)

                        # 変化形
                        change_type = (1 if 0 <= html.find('変形一覧') else 2 if 0 <= html.find('活用表') else 0)
                        if 0 == change_type:
                            changes = ['']
                        else:
                            change_col = html[html.find('変形一覧') if 1 == change_type else html.find('活用表'):]
                            change_col = change_col[: change_col.find('イディオムやフレーズ')]
                            change_col = change_col[: change_col.find('</div>')]

                            if 1 == change_type:
                                change_col = change_col[change_col.find('<table'): change_col.rfind('</table>')]
                                change_col = change_col[: change_col.rfind('</span>')]
                                change_col = change_col[change_col.find('conjugateRowL'):]
                                change_col = change_col[change_col.find('>') + 1:].split('</span>')

                                changes = []
                                for col in change_col:
                                    while 0 <= col.find('<'):
                                        col = col.replace(col[col.find('<'): col.find('>') + 1], '').strip()
                                    changes.append((col if 0 <= col.find('(') else ''))
                            else:
                                change_col = change_col[change_col.find('<th'): change_col.rfind('</table>')]
                                change_col = change_col.split('</tr>')
                                change_col[0] = change_col[0].replace('<tr>', '').split('</th>')
                                change_col[1] = change_col[1].replace('<tr>', '').split('</td>')

                                changes = []
                                for i in range(0, len(change_col[0]) - 1):
                                    if change_col[0][i].find('原型') < 0:
                                        changes.append(change_col[1][i].replace('<td>', '') + '(' +
                                                       change_col[0][i].replace('<th>', '') + ')')

                        # 例文
                        example_col = html[html.find('該当件数'):]
                        example_col = example_col[example_col.find('例文'): example_col.rfind('<span>')]
                        example_col = example_col[example_col.find('<div'):]
                        example_col = example_col.split('<span>&nbsp;-&nbsp;')

                        examples = []
                        for col in example_col:
                            txts = col.split('</div>')

                            for txt in txts:

                                if txt.find('<div') < 0:
                                    continue

                                while 0 <= txt.find('<!'):
                                    txt = txt.replace(txt[txt.find('<!'): txt.find('->') + 2], '')

                                eng = txt[txt.find('<p'): txt.find('>発音を聞く')]
                                eng = eng[eng.find('>') + 1: eng.rfind('<')]
                                eng = eng.replace('<b>', '').replace('</b>', '').replace('</a>', '')
                                eng = eng.split('<span')[0]

                                while 0 <= eng.find('<a '):
                                    eng = eng.replace(eng[eng.find('<a '): eng.find('>') + 1], '')

                                jpn = txt[txt.find('<p') + 1:]
                                jpn = jpn[jpn.find('<p') + 1:]
                                jpn = jpn[jpn.find('>') + 1:]

                                examples.append(eng + ' | ' + jpn)

                        word[target] = {
                            'pronounce': pronounce, 'meaning': meaning, 'partspeech': partspeech,
                            'changes': changes, 'examples': examples}
                        words.append(word)

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        count += 1
                        run_time = com.time_end(start_time)
                        total_times += run_time
                        com.log('Weblio(' + com.conv_time_str(run_time) + '): Lv' +
                                str(lv) + ', ' + target + '(' + str(count) + ')')

                if 0 < len(words):
                    insert_datas.append(words)
                else:
                    insert_datas.append('')

                com.log('Weblio(' + com.conv_time_str(total_times) + '): Lv' + str(lv))
                window.close()

                if not insert:
                    with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Weblio_' + str(lv) + '.json', 'w') as out_file:
                        json.dump({lv: words}, out_file, ensure_ascii=False, indent=4)

            if insert:
                with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Weblio_0.json', 'w') as out_file:
                    json.dump({lv: insert_datas[lv - 1] for lv in range(1, len(insert_datas) + 1)
                               if 0 < len(insert_datas[lv - 1])}, out_file, ensure_ascii=False, indent=4)

        except Exception as e:
            com.log(self.myjob + ' コンテンツ作成 エラー発生: [Lv' + str(lv) + ', ' + target + '] ' + str(e), lv='W')
            com.dialog(self.myjob + ' コンテンツ作成 でエラーが発生しました。\n[Lv' +
                       str(lv) + ', ' + target + ']\n' + str(e), title='エラー発生', lv='W')
            return False

        finally:
            try: window.close()
            except: pass
            try: wd.quit()
            except: pass

        return True

    # 英ナビ取得
    def _get_Einavi(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd_error = 0
        insert = '追加' == selects[0].split('_')[1]

        try:
            datas = open(cst.TEMP_PATH[cst.PC] + 'English/' +
                         ('Einavi' if insert else 'Master') + '.csv', 'r').read().split('\n')
            if insert:
                selects = ['追加_' + str(k) for k in range(1, cst.ENGLISH_MASTER_LEVEL + 1)]
            insert_datas = []

            for select in selects:

                lv = int(select.split('_')[1])
                rows = [row for row in datas if str(lv) == row.split(',')[0]]

                words = []
                total_times = 0
                count = 0

                window = com.progress(self.myjob, ['lv', cst.ENGLISH_MASTER_LEVEL],
                                      ['target', len(rows)], interrupt=True)
                event, values = window.read(timeout=0)

                for row in rows:

                    word = {}
                    cols = row.split(',')
                    targets = cols[1].split('-' if 0 <= cols[1].find('-') else ' ')
                    start_time = com.time_start()

                    # 単語個別のHTML取得を、1分まで実施
                    for target in targets:

                        is_html = False
                        for i in range(0, 60):

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return None

                            window['lv'].update(('追加: ' if insert else '') + 'Lv ' + str(lv) + '/' +
                                                str(cst.ENGLISH_MASTER_LEVEL) + ' [' + str(i + 1) +
                                                ', wd' + str(wd_error) + ']')
                            window['lv_'].update(lv - 1)
                            window['target'].update(target + ' ' + str(count + 1) + '/' + str(len(rows)))
                            window['target_'].update(count)

                            try:
                                wd.get(cst.ENGLISH_DICT_URL['英ナビ'][0] % target)
                                html = wd.page_source
                                html = html[html.find('<!-- word_head -->'):]

                                is_html = True
                                break
                            except:
                                wd_error += 1
                                try: wd.quit()
                                except: pass
                                try: wd = web_driver.driver(headless=IS_HEADLESS)
                                except: pass
                                com.sleep(1)

                        if not is_html:
                            com.log('HTML取得ミス: Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target, lv='W')
                            com.dialog('HTMLを取得ミスしました。\n　Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target,
                                       title='HTML取得ミス', lv='W')
                            return False

                        if 0 == len(html):
                            com.log('対象なし' + str(lv) + ' - ' + str(count + 1) + ' ' + target)

                        htmls = html.split('WordNet')
                        html = htmls[0][htmls[0].find('detail_area'):]

                        if 0 <= html.find('class="entry_group"'):
                            text = htmls[0]
                        else:
                            try:
                                html = htmls[1][: htmls[1].find('<div class="dic_copyright">')]
                                text = html[html.find('<div class="muted_wrap">'): html.find('word_detail')]
                                text = text[: text.rfind('</div>')]
                            except:
                                com.log('Web検索なし: ' + str(lv) + ' - ' + str(count + 1) + ' ' + target)

                        texts = text.split('<div class="muted_wrap">')

                        # 品詞、和訳
                        partspeeches = []
                        meaning = ''
                        for k in range(1, len(texts)):

                            text = texts[k]
                            text = text[:text.find('</div>')]
                            text = text.split('<span>')

                            partspeech = ''
                            for m in range(1, len(text)):
                                partspeech += ('' if 0 == len(partspeech) else ',') + text[m][: text[m].find('</span>')]

                            partspeeches.append(partspeech)

                            # 和訳
                            text = texts[k]
                            text = text[text.find('</div>'):]
                            text = text[text.find('<a'):]
                            text = text[text.find('>') + 1: text.find('</a>')]

                            meaning += ('' if 0 == len(text) else '、') + text

                        # 発音表記
                        pronounce = html[html.find('<h3'):]
                        pronounce = pronounce[pronounce.find('pronunciation-ipa'):]
                        pronounce = pronounce[pronounce.find('>') + 1: pronounce.find('</small>')]
                        pronounce = pronounce.replace('/', '').strip()

                        # 変化形
                        texts1 = html.split('<h3 class="list-group-item-heading">')

                        changes = []
                        for k in range(1, len(texts1)):

                            text = texts1[k]
                            text = text[: text.find('<section>')]
                            texts2 = text.split('</li>')

                            for m in range(0, len(texts2)):

                                text = texts2[m]
                                text = text[text.find('<li'):]
                                text = text[text.find('>') + 1:]

                                if 0 <= text.find('<span>'):
                                    text = text[text.find('<span>'):].replace('&nbsp;', '')
                                    texts3 = text[text.find('>') + 1:].split('</span>')

                                    if 1 < len(texts3[1]):
                                        if 0 <= texts3[1].find('pronunciation-ipa'):
                                            texts3[1] = texts3[1].split('/')[0]

                                        if 0 < len(texts3[1].replace('\n', '').replace('\t', '')):
                                            changes.append(texts3[1] + '(' + texts3[0] + ')')

                        # その他
                        texts1 = html.split('related_words')

                        others = []
                        for k in range(1, len(texts1)):

                            text = texts1[k]
                            text = text[: text.find('</div>')]

                            jpn = text[text.find('<dt>'):].replace('&nbsp;', '')
                            jpn = jpn[jpn.find('>') + 1: jpn.find('</dt>')]

                            if 0 <= jpn.find('<span>'):
                                jpn = jpn[jpn.find('<span>'):]
                                jpn = jpn[jpn.find('>') + 1: jpn.find('</span>')]

                            if 0 == len(jpn):
                                continue

                            eng = ''
                            texts2 = text.split('</a>')
                            for m in range(0, len(texts2)):

                                text = texts2[m]
                                text = text[text.find('<a'):]
                                text = text[text.find('>') + 1:].replace('\t', '')

                                if 0 < len(text):
                                    eng += ('' if 0 == len(eng) else ', ') + text

                            others.append(jpn + '(' + eng + ')')

                        # 例文
                        text = html[html.find('<div class="example_wrap"'):]
                        texts = text.split('</ul>')

                        examples = []
                        for k in range(0, len(texts)):
                            text = texts[k]

                            eng = text[text.find('<li class="en">'):]
                            eng = eng[: eng.find('</li>')]
                            eng = eng[eng.find('>') + 1:].replace('<span>', '').replace('</span>', '')
                            while 0 <= eng.find('<'):
                                eng = eng.replace(eng[eng.find('<'): eng.find('>') + 1], '')

                            jpn = text[text.find('<li class="ja">'):]
                            jpn = jpn[: jpn.find('</li>')]
                            jpn = jpn[jpn.find('>') + 1:].replace('<span>', '').replace('</span>', '')
                            while 0 <= jpn.find('<'):
                                jpn = jpn.replace(jpn[jpn.find('<'): jpn.find('>') + 1], '')

                            if 0 < len(eng):
                                examples.append(eng + ' | ' + jpn)

                        if 0 == len(examples):
                            text = html[html.find('<span class="dict-sp-sentence-pattern">'):]
                            texts = text.split('</blockquote>')

                            for k in range(0, len(texts)):
                                text = texts[k]
                                text = text[text.find('<blockquote class="dict-sp-example">'):]

                                eng = text[text.find('<p'):]
                                eng = eng[eng.find('>') + 1: eng.find('</p>')]
                                while 0 <= eng.find('<'):
                                    eng = eng.replace(eng[eng.find('<'): eng.find('>') + 1], '')
                                eng = eng.split('tatoeba.org')[0].strip()

                                jpn = text[text.find('<p') + 1:]
                                jpn = jpn[jpn.find('<p'):]
                                jpn = jpn[jpn.find('>') + 1: jpn.find('</p>')]
                                while 0 <= jpn.find('<'):
                                    jpn = jpn.replace(jpn[jpn.find('<'): jpn.find('>') + 1], '')
                                jpn = jpn.split('tatoeba.org')[0].strip()

                                if 0 < len(eng):
                                    examples.append(eng + ' | ' + jpn)

                        # mp3のURL
                        mp3 = html[html.find('<audio'):]
                        mp3 = mp3[mp3.find('>') + 1: mp3.find('</audio')]
                        mp3 = mp3[mp3.find('src='): mp3.find('type=')]
                        mp3 = mp3[mp3.find('"') + 1: mp3.rfind('"')]

                        word[target] = {
                            'pronounce': pronounce, 'meaning': meaning, 'partspeech': partspeeches,
                            'changes': changes, 'examples': examples, 'others': others, 'mp3': mp3}
                        words.append(word)

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        count += 1
                        run_time = com.time_end(start_time)
                        total_times += run_time
                        com.log('Einavi(' + com.conv_time_str(run_time) + '): Lv' +
                                str(lv) + ', ' + target + '(' + str(count) + ') ' + pronounce +
                                (' :' + str(partspeeches) + str(changes) + str(examples) + str(others)
                                 if 0 == len(examples) else ''))

                if 0 < len(words):
                    insert_datas.append(words)
                else:
                    insert_datas.append('')

                com.log('Einavi(' + com.conv_time_str(total_times) + '): Lv' + str(lv))
                window.close()

                if not insert:
                    with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Einavi_' + str(lv) + '.json', 'w') as out_file:
                        json.dump({lv: words}, out_file, ensure_ascii=False, indent=4)

            if insert:
                with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Einavi_0.json', 'w') as out_file:
                    json.dump({lv: insert_datas[lv - 1] for lv in range(1, len(insert_datas) + 1)
                               if 0 < len(insert_datas[lv - 1])}, out_file, ensure_ascii=False, indent=4)

        except Exception as e:
            com.log(self.myjob + ' コンテンツ作成 エラー発生: [Lv' + str(lv) + ', ' + target + '] ' + str(e), lv='W')
            com.dialog(self.myjob + ' コンテンツ作成 でエラーが発生しました。\n[Lv' +
                       str(lv) + ', ' + target + ']\n' + str(e), title='エラー発生', lv='W')
            return False

        finally:
            try: window.close()
            except: pass
            try: wd.quit()
            except: pass

        return True

    # Google取得
    def _get_google(self, selects):

        wd = web_driver.driver()
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd_error = 0
        insert = '追加' == selects[0].split('_')[1]

        try:
            datas = open(cst.TEMP_PATH[cst.PC] + 'English/' +
                         ('Google' if insert else 'Master') + '.csv', 'r').read().split('\n')
            if insert:
                selects = ['追加_' + str(k) for k in range(1, cst.ENGLISH_MASTER_LEVEL + 1)]
            insert_datas = []

            for select in selects:

                lv = int(select.split('_')[1])
                rows = [row for row in datas if str(lv) == row.split(',')[0]]

                old_data = ''
                words = []
                total_times = 0
                count = 0

                window = com.progress(self.myjob, ['lv', cst.ENGLISH_MASTER_LEVEL],
                                      ['target', len(rows)], interrupt=True)
                event, values = window.read(timeout=0)

                for row in rows:

                    word = {}
                    cols = row.split(',')
                    targets = cols[1].split('-' if 0 <= cols[1].find('-') else ' ')
                    start_time = com.time_start()

                    # 単語個別のHTML取得を、1分まで実施
                    for target in targets:
                        while True:

                            pos_x, pos_y = pgui.position()
                            wd.get(cst.ENGLISH_DICT_URL['Google'][0] % '')
                            com.sleep(1)

                            sec = 0
                            is_match = False

                            while sec < 5:

                                # 中断イベント
                                if _is_interrupt(window, event):
                                    return None

                                window['lv'].update(('追加: ' if insert else '') + 'Lv ' + str(lv) + '/' +
                                                    str(cst.ENGLISH_MASTER_LEVEL) + ' [' + str(sec + 1) +
                                                    ', wd' + str(wd_error) + ']')
                                window['lv_'].update(lv - 1)
                                window['target'].update(target + ' ' + str(count + 1) + '/' + str(len(rows)))
                                window['target_'].update(count)

                                try:
                                    wd.get(cst.ENGLISH_DICT_URL['Google'][0] % target)
                                    com.sleep(1)

                                    for _ in range(0, 5):

                                        shot, gray = com.shot_grab()
                                        x, y = com.match(shot, gray, cst.MATCH_PATH + 'english/google_trans.png',
                                                         (0, 0, 255))

                                        if x is None:
                                            com.sleep(1)
                                            continue

                                        is_match = True
                                        break

                                    break
                                except:
                                    wd_error += 1
                                    try: wd.quit()
                                    except: pass
                                    try: wd = web_driver.driver()
                                    except: pass
                                    com.sleep(1)

                            if not is_match:
                                com.log('マッチングエラー: Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target, lv='W')

                            try:
                                pgui.click(int(x / 2 - 100), int(y / 2 + 20), clicks=2, interval=0, button='left')
                            except:
                                try:
                                    pgui.click(700, 700, clicks=2, interval=0, button='left')
                                except:
                                    com.move_pos(pos_x, pos_y)
                                    com.log('クリックエラー: Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target, lv='W')
                                    count += 1
                                    continue

                            com.sleep(1)
                            pgui.hotkey('command', 'a')
                            pgui.hotkey('command', 'c')
                            com.sleep(1)

                            com.move_pos(pos_x, pos_y)
                            data = pyperclip.paste()

                            if data == old_data:
                                continue
                            old_data = data

                            data = data.split('help_outline')

                            pronounce = data[0].split('/')[0].split('\n')
                            pronounce = pronounce[len(pronounce) - (4 if 0 <= pronounce.find('原文の言語') else 2)]

                            meanings = []
                            partspeeches = []

                            try:
                                for k in range(1, len(data[1].split('\n')) - 2):
                                    text = data[1].split('\n')[k]

                                    if re.match(r'([a-z])', text) or re.match(r'([A-Z])', text):
                                        continue
                                    elif len(text) < 0:
                                        continue
                                    elif text.endswith('詞'):
                                        partspeeches.append(text)
                                    else:
                                        meanings.append(text)
                            except:
                                partspeeches.append('')
                                meanings.append('')

                            word[target] = {
                                'pronounce': pronounce, 'meaning': list(set(meanings)), 'partspeech': partspeeches}
                            words.append(word)

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return None

                            count += 1

                            run_time = com.time_end(start_time)
                            total_times += run_time
                            com.log('Google(' + com.conv_time_str(run_time) + '): Lv' + str(lv) + ', ' +
                                    target + '(' + str(count) + ') ' + pronounce + (' :' + str(partspeeches)))

                            break

                if 0 < len(words):
                    insert_datas.append(words)
                else:
                    insert_datas.append('')

                com.log('Google(' + com.conv_time_str(total_times) + '): Lv' + str(lv))
                window.close()

                if not insert:
                    with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Google_' + str(lv) + '.json', 'w') as out_file:
                        json.dump({lv: words}, out_file, ensure_ascii=False, indent=4)

            if insert:
                with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Google_0.json', 'w') as out_file:
                    json.dump({lv: insert_datas[lv - 1] for lv in range(1, len(insert_datas) + 1)
                               if 0 < len(insert_datas[lv - 1])}, out_file, ensure_ascii=False, indent=4)

        except Exception as e:
            com.log(self.myjob + ' コンテンツ作成 エラー発生: [Lv' + str(lv) + ', ' + target + '] ' + str(e), lv='W')
            com.dialog(self.myjob + ' コンテンツ作成 でエラーが発生しました。\n[Lv' +
                       str(lv) + ', ' + target + ']\n' + str(e), title='エラー発生', lv='W')
            return False

        finally:
            try: window.close()
            except: pass
            try: wd.quit()
            except: pass

        return True

    # Content.json作成
    def _merge_content(self, _):

        base_file = cst.TEMP_PATH[cst.PC] + 'English/dict/' + FUNCTIONS[2][2] + '.' + FUNCTIONS[2][3]
        plus_file = cst.TEMP_PATH[cst.PC] + 'English/dict/' + FUNCTIONS[1][2] + '.' + FUNCTIONS[1][3]
        google_file = cst.TEMP_PATH[cst.PC] + 'English/dict/' + FUNCTIONS[3][2] + '.' + FUNCTIONS[3][3]

        merges = {}
        out_counts = [0 for _ in range(0, int(cst.ENGLISH_MASTER_LEVEL / 2))]

        plus = {}
        for lv in range(0, cst.ENGLISH_MASTER_LEVEL + 1):

            file = open(plus_file.replace(
                FUNCTIONS[1][2] + '.', FUNCTIONS[1][2] + '_' + str(lv) + '.'), encoding='utf8').read()

            file = json.loads(file)
            for col in file:
                for i in range(0, len(file[col])):
                    for key in file[col][i]:
                        plus[key] = file[col][i][key]

        google = {}
        for lv in range(0, cst.ENGLISH_MASTER_LEVEL + 1):

            file = open(google_file.replace(
                FUNCTIONS[3][2] + '.', FUNCTIONS[3][2] + '_' + str(lv) + '.'), encoding='utf8').read()
            file = json.loads(file)

            for col in file:
                for i in range(0, len(file[col])):
                    for key in file[col][i]:
                        google[key] = file[col][i][key]

        insert_file = open(base_file.replace(
            FUNCTIONS[2][2] + '.', FUNCTIONS[2][2] + '_0.'), 'r', encoding='utf8').read()
        insert_file = json.loads(insert_file)

        rows = []
        merge = []
        mp3s = {}
        change_irregular = {}

        for lv in range(1, cst.ENGLISH_MASTER_LEVEL + 1):

            file = pd.read_json(base_file.replace(
                FUNCTIONS[2][2] + '.', FUNCTIONS[2][2] + '_' + str(lv) + '.'), encoding='utf8')
            for key in file:
                rows.append(file[key])

            if 0 == lv % 2:
                merge.append(rows)
                rows = []

        for lv in range(1, len(merge) + 1):

            old_keys = []
            new_keys = []
            old_datas = []
            new_datas = []

            try:
                insert = insert_file[str(lv)]
            except:
                insert = []

            if 0 < len(insert):

                datas = pd.DataFrame(pd.Series(insert), columns=[1])
                for i in datas:
                    for data in datas[i]:
                        for key in data:
                            old_keys.append(key)
                            new_keys.append(key.lower())
                            old_datas.append({key: data[key]})

            for words in merge[lv - 1]:
                for word in words:
                    for key in word:
                        old_keys.append(key)
                        new_keys.append(key.lower())
                        old_datas.append({key: word[key]})

            new_keys.sort()
            for key1 in new_keys:

                is_append = False
                for data in old_datas:

                    for key2 in data:
                        if key1 == key2.lower():

                            try:
                                if new_datas[len(new_datas) - 1][key2] is not None:
                                    continue
                            except:
                                pass

                            new_datas.append({key2: data[key2]})
                            is_append = True
                            break

                    if is_append:
                        break

                merges[lv] = new_datas

            rows = []
            old_pronounce = ''
            old_meaning = ''

            for words in merges[lv]:
                word = {}

                for key in words:

                    # a・I・数字・Mr関係の除外と、特定狙い撃ち除外
                    if len(key) < 2 or key.endswith('tieth') or key.endswith('teenth') or key.endswith('.')\
                            or key in ['am']:
                        out_counts[lv - 1] += 1
                        com.log('特定ワード除外: ' + key)
                        continue

                    # Googleの整合性チェック
                    if google[key]['pronounce'] == old_pronounce and google[key]['meaning'] == old_meaning:
                        com.log('pronounce重複: ' + key)
                    old_pronounce = google[key]['pronounce']
                    old_meaning = google[key]['meaning']

                    # 発音がWeblioにない場合
                    pronounce = plus[key]['pronounce']
                    inclosures = ['〈', '〉']
                    if 0 == len(pronounce):

                        # 発音が英ナビにない場合、Google使用
                        if 0 == len(words[key]['pronounce']):
                            pronounce = google[key]['pronounce']
                            inclosures = [' [', ']']

                        # 英ナビを使用する場合
                        else:
                            pronounce = words[key]['pronounce'].replace('&nbsp;', ' ')
                            inclosures = [' {', '}']

                    # 発音がWeblioにある場合、優先使用
                    else:
                        pronounces = pronounce.split(',')
                        pronounce = ''
                        for i in range(0, len(pronounces)):
                            if 0 <= pronounces[i].find('(米国'):

                                pronounces[i] = pronounces[i].replace('--', '')

                                # "-"がある場合は、英国を使用
                                if 0 <= pronounces[i].find('‐') or 0 <= pronounces[i].find('ˈ-'):
                                    try:
                                        pronounce = pronounces[i + 1][:pronounces[i + 1].find('(英国')].strip()

                                    # 英国がなければ、Googleを使用
                                    except:
                                        pronounce = google[key]['pronounce']
                                        inclosures = [' [', ']']

                                    # 最終的に"-"が残る場合は、Googleを使用
                                    if 0 <= pronounce.find('‐'):
                                        pronounce = google[key]['pronounce']
                                        inclosures = [' [', ']']

                                # 通常は米国を使用
                                else:
                                    if 0 <= pronounces[i].find('》'):
                                        pronounces[i] = pronounces[i].split('》')[1]
                                    pronounce = pronounces[i][:pronounces[i].find('(米国')].strip()

                                if 0 <= pronounce.find(' '):
                                    pronounce = pronounce.split(' ')[1]

                                if 0 <= pronounce.find('形'):
                                    pronounce = pronounce.split(')')[1]

                    # 発声の文字変換(Google)
                    pronounce = pronounce.replace('TH', 'ð').replace('T͟H', 'θ'). \
                        replace('SH', 'ʃ').replace('ZH', 'dʒ').replace('NG', 'ˈŋ'). \
                        replace('o͟o', 'ōō').replace('o͞o', 'úː').replace('o͝o', 'ˈʊ')
                    words[key]['pronounce'] = inclosures[0] + pronounce + inclosures[1]

                    # 英ナビに品詞がある場合は編集
                    if 0 < len(words[key]['partspeech']):
                        texts = words[key]['meaning'].replace('（', '(').replace('）', ')')
                        texts = texts.replace('，', '、').strip().split('、')
                        meanings = []

                        for text in texts:
                            if 0 < len(text):
                                meanings.append(text)

                        words[key]['meaning'] = meanings

                        partspeeches = []
                        for i in range(0, len(words[key]['partspeech'])):

                            texts = words[key]['partspeech'][i].split(',')
                            text = ''

                            for k in range(0, len(texts)):
                                if texts[k] in ['動', '名']:

                                    char = ''
                                    for txt in plus[key]['partspeech']:

                                        if 0 <= txt.find('自動詞'):
                                            char += '自,'
                                        elif 0 <= txt.find('他動詞'):
                                            char += '他,'
                                        elif 0 <= txt.find('不可算名詞'):
                                            char += 'U,'
                                        elif 0 <= txt.find('可算名詞'):
                                            char += 'C,'
                                        elif 0 <= txt.find('形容詞'):
                                            char += ('形容詞,' if char.find('形容詞') < 0 else '')
                                        elif 0 < len(txt):
                                            char += (txt + ',' if char.find(txt) < 0 else '')
                                        else:
                                            char += ('名詞,' if char.find('名詞') < 0 else '')

                                    if 0 <= char.find('自') or 0 <= char.find('他'):
                                        text += ('' if 0 == len(text) else ',') + '動詞(自・他)'
                                    elif 0 <= char.find('自'):
                                        text += ('' if 0 == len(text) else ',') + '動詞(自)'
                                    elif 0 <= char.find('他'):
                                        text += ('' if 0 == len(text) else ',') + '動詞(他)'

                                    if 0 <= char.find('U') or 0 <= char.find('C'):
                                        text += ('' if 0 == len(text) else ',') + '名詞(可算・不可算)'
                                    elif 0 <= char.find('U'):
                                        text += ('' if 0 == len(text) else ',') + '名詞(可算)'
                                    elif 0 <= char.find('C'):
                                        text += ('' if 0 == len(text) else ',') + '名詞(不可算)'

                                    text += ('' if 0 == len(text) else ',')
                                    text += char.replace('自,', '').replace('他,', '').replace('U,', '').replace('C,', '')
                                    text = text[: -1]

                                # 動詞と名詞以外
                                else:
                                    text += ('' if 0 == len(text) else ',')
                                    text += cst.EINAVI_PARTSPEECH[texts[k]]

                            text = '名詞' if 0 == len(text) else text.split(',')
                            partspeeches.append(text)

                        texts = []
                        for lists in partspeeches:
                            for text in lists:
                                texts.append(text)

                        words[key]['partspeech'] = list(set(texts))

                    # 和訳にWeblio追記
                    meaning = plus[key]['meaning']
                    meaning_kana = []
                    if (0 <= meaning.find('の') and 'could' != key
                            and (0 <= meaning.find('分詞') or 0 <= meaning.find('過去形')
                                 or 0 <= meaning.find('人称単数現在') or 0 <= meaning.find('複数形'))) \
                            or 'are' == key:
                        com.log('変化形(meaning)除外: ' + str(lv) + ', ' + key + ' | ' + meaning)
                        out_counts[lv - 1] += 1
                        continue

                    # 意味の編集
                    if 0 <= meaning.find('対訳は、'):
                        meaning = meaning.split('対訳は、')[1]

                    meanings = []
                    for txt in meaning.replace('；', '、').split('、'):

                        txt = txt.replace('（', '(').replace('）', ')')
                        if txt.find(')') < 0 <= txt.find('('):
                            txt = txt.split('(')[0].strip()
                        elif txt.find('(') < 0 <= txt.find(')') \
                                or 0 <= txt.find('表記)') or 0 <= txt.find('などです。'):
                            continue

                        txt = txt.replace('(通例', '(').replace('通例 ', '')
                        txt = txt.replace('…', '〜').replace('・', '．')
                        for check in ['(〜を)', '(〜の)', '(〜に)', '(〜へ)', '(〜と)',
                                      '(〜は)', '(〜が)', '(〜で)', '(へ)', '(〜ない)']:

                            txt = (txt.replace(check, '') if 0 <= txt.find(check) else txt)

                        meanings.append(txt)
                    meaning = "、".join(txt for txt in meanings)

                    # (())
                    while 0 <= meaning.find('('):

                        # 1 ( 2 ) 3
                        txt1 = meaning[: meaning.find('(')]
                        txt2 = meaning[meaning.find('(') + 1:]
                        txt3 = txt2[txt2.find(')') + 1:]

                        txt = txt2[: txt2.find(')')]
                        next_no = meaning.find(')') + txt3.find('、')

                        # ()通常、中に"、"あり、次の和訳あり (、)、
                        if meaning.find('(') < meaning.find('(') + txt.find('、') < meaning.find(')') <= \
                                next_no:
                            meaning = txt1 + '{' + txt.replace('、', '．') + '}'
                            meaning += txt3

                        # ()通常、中に"、"なし、次の和訳あり ()、
                        elif meaning.find('(') < meaning.find(')') <= next_no:
                            meaning = txt1 + '{' + txt + '}'
                            meaning += txt3

                        # ()通常、中に"、"あり、次の和訳なし (、)
                        elif next_no < 0 < \
                                meaning.find('(') < meaning.find('(') + txt.find('、') < meaning.find(')'):
                            meaning = txt1 + '{' + txt.replace('、', '．') + '}'

                        # ()通常、中に"、"なし、次の和訳なし ()
                        elif next_no < 0 < meaning.find('(') < meaning.find(')'):
                            meaning = txt1 + '{' + txt + '}'

                        # )なしの場合
                        else:
                            # 次の和訳あり (、
                            if 0 <= meaning.find('、'):
                                meaning = txt1 + '{' + txt2[: txt2.find('、')].replace(')', '}')
                                meaning += txt2[txt2.find('、'):]

                            # 次の和訳なし (
                            else:
                                meaning = txt1 + '{' + txt2.replace(')', '}')

                    meanings = meaning.replace('{', '(').replace('}', ')').split('、')
                    meaning = []
                    for i in range(0, len(meanings)):

                        is_meaning = True
                        for k in range(0, len(meaning)):

                            if 0 <= meaning[k].find(meanings[i].split('(')[0]) \
                                    or meaning[k].replace('「', '').replace('」', '') == \
                                    meanings[i].replace('「', '').replace('」', '') \
                                    or meaning[k].replace(meaning[k][meaning[k].find('['): meaning[k].rfind(']')],
                                                          '') == \
                                    meanings[i].replace(meanings[i][meanings[i].find('['): meanings[i].rfind(']')], ''):
                                is_meaning = False
                                break

                        if is_meaning:
                            txt = meanings[i].split('。')[1] \
                                if 0 <= meanings[i].find('。') else meanings[i]
                            meaning.append(txt)
                            kks = pykakasi.kakasi()
                            kks.setMode('J', 'H')
                            meaning_kana.append(kks.getConverter().do(txt))

                    texts = [text.replace('}', ')') for text in meaning if text.find('《1') < 0]
                    meanings = words[key]['meaning']
                    meanings = ([] if 0 == len(meanings) else meanings)

                    for text in texts:
                        if 0 < len(text):
                            meanings.append(text.replace('，', '、').strip())

                    words[key]['meaning'] = meanings + google[key]['meaning']

                    # 品詞がない場合、Weblio使用
                    if 0 == len(words[key]['partspeech']):
                        partspeeches = []
                        txts = []

                        if 0 == len(plus[key]['partspeech']):
                            plus[key]['partspeech'] = ['名詞']

                        for txt in plus[key]['partspeech']:

                            # 形容詞の単一化
                            txt = txt.replace('(限定用法の形容詞)', '').replace('(叙述的用法の形容詞)', '')

                            # 動詞の編集
                            if txt.startswith('自動詞'):
                                txt = txt.replace('自動詞', '動詞(自)')
                            if txt.startswith('他動詞'):
                                txt = txt.replace('他動詞', '動詞(他)')
                            if txt.startswith('動詞(自動詞)'):
                                txt = txt.replace('自動詞', '自')
                            if txt.startswith('動詞(他動詞)'):
                                txt = txt.replace('他動詞', '他')

                            # 名詞の編集
                            if 0 <= txt.find('可算名詞'):
                                txt = txt.replace('名詞)', ')')

                            txts.append(txt)
                        txts = list(set(txts))

                        # 動詞と名詞は、2種類あればひとまとめ
                        v_count = 0
                        n_count = 0
                        for txt in txts:
                            if 0 <= txt.find('自') or 0 <= txt.find('他'):
                                v_count += 1
                            elif 0 <= txt.find('可算'):
                                n_count += 1
                            else:
                                partspeeches.append(txt)

                        for txt in txts:
                            if 0 <= txt.find('動詞(') and 2 == v_count:
                                partspeeches.append('動詞(自・他)')
                            elif 0 <= txt.find('名詞(') and 2 == n_count:
                                partspeeches.append('名詞(可算・不可算)')
                            elif 0 <= txt.find('可算名詞(不可算)') or 0 <= txt.find('不可算名詞(可算)'):
                                partspeeches.append('名詞(可算・不可算)')
                            else:
                                partspeeches.append(txt)

                        # 品詞の重複を削除
                        plus[key]['partspeech'] = list(set(partspeeches))

                        # 品詞の「動詞」「名詞」を編集
                        partspeeches = []
                        for txt in plus[key]['partspeech']:
                            is_txt = True

                            if txt in ['動詞', '名詞']:
                                is_txt = True

                                for txt2 in plus[key]['partspeech']:
                                    if txt != txt2 and txt2.startswith(txt):
                                        is_txt = False
                            if is_txt:
                                partspeeches.append(txt)

                        words[key]['partspeech'] = partspeeches

                    # 変化形がない場合、Weblio使用
                    if 0 == len(words[key]['changes']):

                        # 変化形の「●詞：」を除去
                        changes = []
                        for txt in plus[key]['changes']:

                            if 0 <= txt.find('(原形)'):
                                continue

                            elif 0 <= txt.find(','):
                                txt = txt.split(',')[len(txt.split(',')) - 1].strip()

                            txt = txt.split('：')[1] if 0 <= txt.find('：') else txt

                            if 0 < len(txt):
                                changes.append(txt)

                        words[key]['changes'] = changes

                    # 変化形がある場合の編集
                    else:
                        words[key]['changes'] = list(set(
                            [change.replace('分詞形', '分詞').replace('現在形', '現在')
                             for change in words[key]['changes'] if change.find('〜') < 0]))

                    example = []

                    # 例文がある場合は編集
                    if 0 < len(words[key]['examples']):
                        examples = words[key]['examples']
                        for i in range(0, len(examples)):
                            eng = examples[i].split('|')[0]
                            jpn = examples[i].split('|')[1]

                        if 100 < len(eng):
                            continue

                        eng = eng.replace('\"', '').strip()
                        jpn = jpn.replace('（', '(').replace('）', ')').replace('\"', '').strip()

                        if 0 < len(eng) and 0 < len(jpn):
                            example.append(eng + ' | ' + jpn)

                    # 例文が少ない場合、Weblioの例文を連結
                    if len(example) <= 5:

                        examples = plus[key]['examples']
                        for i in range(0, len(examples)):

                            eng = examples[i].split('|')[0]
                            jpn = examples[i].split('|')[1]

                            if 100 < len(eng) or 0 <= examples[i].find('://'):
                                continue
                            if re.match(r'([a-z])', jpn.strip()) or re.match(r'([A-Z])', jpn.strip()) \
                                    or re.match(r'/', jpn.strip()) or 0 <= jpn.find('年生まれ'):
                                continue

                            if 0 <= eng.find(key.upper()) or key == eng.strip() \
                                    or 0 <= examples[i].find('＜') or 0 <= examples[i].find('年−') \
                                    or 0 <= examples[i].find('Memory\',') \
                                    or 0 <= examples[i].find('also called') < examples[i].find('とも呼ばれる。'):
                                continue

                            eng = eng.replace('（を略して通例）', ' ')

                            if eng[2:].find('\"') < eng.find('\"') == 0:
                                jpn = jpn.replace('「', '')

                            # 細かい整形
                            eng = eng.replace('―', ' - ').replace('＝', ' / ').replace('；', ' / ').replace('()', '')
                            eng = eng.replace(eng[eng.find('〈'): eng.rfind('〉')], '')
                            eng = eng.replace(eng[eng.find('《'): eng.rfind('》')], '')

                            eng = eng.replace('（', '(').replace('）', ')')
                            eng = eng.replace('&amp;amp;', '＆').replace('&amp;', '＆').replace('&nbsp;', ' ')
                            eng = eng.replace('&gt;', ' ').replace('\"', '')
                            eng = eng.replace('+-', '').replace('-+', '').replace('---', '')
                            eng = eng.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                            eng = eng.replace('{', '').replace('}', '').replace('__', '')
                            eng = eng.replace('》', '').replace('〉', '').strip()

                            if eng.endswith('.') or eng.endswith(','):
                                eng = eng[:-1]
                            if eng.startswith(','):
                                eng = eng[1:].strip()

                            jpn = jpn.replace('()', '').replace('\"', '')
                            jpn = jpn.replace(jpn[jpn.find('《'): jpn.rfind('》')], '')

                            jpn = jpn.replace('（', '(').replace('）', ')')
                            jpn = jpn.replace('&amp;amp;', '＆').replace('&amp;', '＆').replace('&nbsp;', ' ')
                            jpn = jpn.replace('<b>', '').replace('</b>', '').replace('》', '').strip()

                            if jpn.endswith('.') or jpn.endswith('；') or jpn.endswith('：') or jpn.endswith('。'):
                                jpn = jpn[:-1].strip()
                            if jpn.startswith('、'):
                                jpn = jpn[1:].strip()

                            # 同一例文の複数和訳まとめ
                            is_example = True
                            for k in range(0, len(example)):

                                texts = example[k].split(' | ')
                                if texts[0].replace('.', '').replace(',', '').replace(';', '').replace(':',
                                                                                                       '').lower() == \
                                        eng.replace('.', '').replace(',', '').replace(';', '').replace(':', '').lower():
                                    is_example = False
                                    break

                            if 0 < len(eng) and 0 < len(jpn):
                                if is_example:
                                    example.append(eng + ' | ' + jpn)

                                elif texts[1].find(jpn) < 0:
                                    example[k] += ' / ' + jpn

                    words[key]['examples'] = example

                    # その他の編集
                    others = []
                    other = words[key]['others']

                    if 0 < len(other):
                        for i in range(0, len(other)):

                            if len(other) <= i:
                                break

                            other1 = other[i].replace(')', '')
                            text = other1.split('(')[1]

                            for k in reversed(range(i + 1, len(other))):
                                other2 = other[k].replace(')', '')

                                if other1.split('(')[0] == other2.split('(')[0]:
                                    text += ',' + other2.split('(')[1]
                                    del words[key]['others'][k]

                            text = text.replace('&amp;#039;', '\'')
                            text = list(set([other.strip() for other in text.split(',') if other.strip() != key]))
                            others.append(other1.split('(')[0] + '(' + ", ".join([other for other in text]) + ')')

                        for k in reversed(range(0, len(others))):
                            if 0 <= others[k].find('()'):
                                others.remove(others[k])

                        words[key]['others'] = others

                    # 最終チェック(partspeech)
                    partspeech = words[key]['partspeech']
                    checks = ['動詞', '名詞']

                    for i in reversed(range(0, len(partspeech))):
                        for check in checks:

                            if len(partspeech) <= i:
                                break

                            if partspeech[i] in check:
                                for k in range(0, len(partspeech)):

                                    if 0 <= partspeech[k].find(check + '('):
                                        del partspeech[i]
                                        break

                    words[key]['partspeech'] = partspeech

                    # 最終チェック(meaning)
                    words[key]['meaning'] = sorted(words[key]['meaning'], reverse=True)
                    for i in reversed(range(0, len(words[key]['meaning']))):

                        words[key]['meaning'][i] = words[key]['meaning'][i].replace(' ', '')
                        meaning = words[key]['meaning'][i]

                        if meaning in IGNORE_MEANINGS:
                            words[key]['meaning'].remove(meaning)
                            continue

                        chk_text = meaning.translate(str.maketrans(
                            {chr(0xFF01 + m): chr(0x21 + m) for m in range(94)}))

                        if 1 < len(words[key]['meaning']) and(len(chk_text) < 2 or 17 < len(chk_text)):
                            words[key]['meaning'].remove(meaning)
                            continue

                        for k in range(0, i):

                            text = words[key]['meaning'][k].translate(str.maketrans(
                                {chr(0xFF01 + m): chr(0x21 + m) for m in range(94)}))

                            if text == chk_text or text.startswith(chk_text + '(') or text.endswith(')' + chk_text):
                                words[key]['meaning'].remove(meaning)
                                break

                    for i in reversed(range(1, len(words[key]['meaning']))):
                        text = words[key]['meaning'][i]

                        if text.startswith('〜'):
                            words[key]['meaning'].remove(text)

                    hira_count = 0
                    kata_count = 0
                    for i in reversed(range(1, len(words[key]['meaning']))):
                        text = words[key]['meaning'][i]

                        if (text.find(')') < 0 <= text.find('(')
                                or text.find('(') < 0 <= text.find(')')):

                            words[key]['meaning'].remove(text)
                        elif 2 == len(text):
                            if re.match(r'([あ-ん])', text):
                                hira_count += 1
                            if re.match(r'([ア-ン])', text):
                                kata_count += 1

                    if 1 <= hira_count:
                        for i in reversed(range(1, len(words[key]['meaning']))):
                            text = words[key]['meaning'][i]

                            if re.match(r'([あ-ん])', text):
                                words[key]['meaning'].remove(text)

                    if 1 <= kata_count:
                        for i in reversed(range(1, len(words[key]['meaning']))):
                            text = words[key]['meaning'][i]

                            if re.match(r'([ア-ン])', text):
                                words[key]['meaning'].remove(text)

                    if 2 < len(words[key]['meaning']):
                        for i in reversed(range(0, len(words[key]['meaning']))):
                            text = words[key]['meaning'][i]

                            if (1 == len(text) or 10 < len(text)) and 5 < len(words[key]['meaning']):
                                words[key]['meaning'].remove(text)
                                continue

                    for i in reversed(range(0, len(words[key]['meaning']))):

                        words[key]['meaning'][i] = (words[key]['meaning'][i].replace('(', '')
                                                    if words[key]['meaning'][i].find(')') < 0 else meaning)
                        words[key]['meaning'][i] = (words[key]['meaning'][i].replace(')', '')
                                                    if words[key]['meaning'][i].find('(') < 0 else meaning)

                    words[key]['meaning'] = list(set(words[key]['meaning']))
                    try:
                        for i in range(0, len(words[key]['meaning'])):

                            text = words[key]['meaning'][i]
                            cnvs = pykakasi.kakasi().convert(text)

                            cnv = "".join([cnv['hira'] for cnv in cnvs])
                            if text != cnv in words[key]['meaning']:
                                words[key]['meaning'].remove(cnv)
                            else:
                                cnv = "".join([cnv['kana'] for cnv in cnvs])
                                if text != cnv in words[key]['meaning']:
                                    words[key]['meaning'].remove(cnv)
                    except: pass

                    words[key]['meaning'] = words[key]['meaning']

                    # 例外処理
                    reg_key = key
                    if 'TRUE' == key:
                        reg_key = key.lower()

                    # 品詞が英ナビにもWeblioにもなく、Googleにある場合はGoogle使用
                    if 0 == len(words[key]['partspeech'][0]) and 0 < len(google[key]['partspeech']):
                        words[key]['partspeech'] = google[key]['partspeech']

                    # 単語に格納
                    if 0 < len(words[key]['partspeech'][0]):
                        word[reg_key] = words[key]
                    else:
                        com.log('partspeechなし: ' + str(lv) + ', ' + key)
                        out_counts[lv - 1] += 1

                    # 変化形の整理
                    if 0 < len(words[key]['changes']):

                        compare = ''
                        for i in reversed(range(0, len(words[key]['changes']))):
                            change = words[key]['changes'][i]

                            if 0 <= change.find('比較級') or 0 <= change.find('最上級'):
                                words[key]['changes'].remove(change)
                                compare += ', ' + change

                        if 0 < len(compare):
                            words[key]['others'].append(compare[2:])

                        changes = []

                        for i in range(0, len(words[key]['changes'])):
                            if 0 <= words[key]['changes'][i].find(','):
                                text = words[key]['changes'][i].split(',')
                                words[key]['changes'][i] = text[len(text) - 1]

                        for i in range(0, len(words[key]['changes'])):
                            changes.append([words[key]['changes'][i].split('(')[0] ,
                                            '(' + words[key]['changes'][i].split('(')[1]])

                        changes = sorted(changes, key=lambda x: x[1], reverse=True)
                        words[key]['changes'] = []
                        countable = ''

                        for i in range(0, len(changes)):
                            change = "".join([text for text in changes[i]])

                            if 0 <= change.find('複数形'):
                                countable = change
                            else:
                                words[key]['changes'].append(change)

                        if 0 < len(countable):
                            words[key]['changes'].append(countable)

                        changes = {key : ['', '']}
                        for change in words[key]['changes']:
                            if 0 <= change.find('過去'):

                                if not change.split('(')[0].endswith('d'):

                                    if 0 <= change.find('過去形'):
                                        changes[key][0] = change
                                    else:
                                        changes[key][1] = change

                        for change in changes:
                            if 0 < len(changes[change][0]) + len(changes[change][1]):
                                change_irregular[change] = changes[change]

                    mp3s[key] = words[key]['mp3']
                    del words[key]['mp3']

                    # 特定狙い撃ち修正
                    if 'be' == key:
                        words[key]['changes'][0] = words[key]['changes'][0].replace('過去形', '二人称複数過去形')
                        words[key]['changes'].insert(0, 'was(三人称単数過去形)')
                        words[key]['changes'].append('are(二人称複数現在形)')
                        words[key]['changes'].append('am(一人称単数形)')

                if 0 < len(word):
                    rows.append(word)

            merges[lv] = rows

        with open(cst.TEMP_PATH[cst.PC] + 'English/MP3.json', 'w') as out_file:
            out_file.write(json.dumps(mp3s, ensure_ascii=False, indent=4))

        with open(cst.TEMP_PATH[cst.PC] + 'English/Content.js', 'w') as out_file:
            out_file.write('const CONTENTS =\n' + json.dumps(merges, ensure_ascii=False, indent=4))

        irregular_verb1 = []
        irregular_verb2 = []
        irregular_verb3 = []
        irregular_verb4 = []

        for change in change_irregular:

            if re.match(r'([A-Z])', change[0]):
                continue

            pasts = change_irregular[change]
            past1 = pasts[0].split('(')[0]
            past2 = pasts[1].split('(')[0]

            if past1 != change == past2:
                irregular_verb3.append(change)
            elif change != past1 == past2:
                irregular_verb2.append(change)
            elif change == past1 == past2:
                irregular_verb4.append(change)
            else:
                irregular_verb1.append(change)

        irregular_verbs = [['不規則(All)'], sorted(irregular_verb1), ['不規則(Past)'], sorted(irregular_verb2),
                           ['不規則(Simple)'], sorted(irregular_verb3), ['無変化'], sorted(irregular_verb4)]

        with open(cst.TEMP_PATH[cst.PC] + 'English/IrregularVerb.js', 'w') as out_file:
            out_file.write('const IRREGULAR_VERB_LISTS =\n' + json.dumps(irregular_verbs, ensure_ascii=False, indent=4))

        com.log('除外件数: ' + str([str(i + 1) + '(' + str(out_counts[i]) + ')'
                                for i in range(0, len(out_counts))]))
        return True

    # MP3ダウンロード
    def _get_mp3(self, selects):

        wd_error = 0
        command = ('POST', '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {
            'behavior': 'allow', 'downloadPath': MP3_PATH}}

        # lm_wd = web_driver.driver()
        # if lm_wd is None:
        #     com.dialog('WebDriver(LONGMAN)で異常が発生しました。', 'WebDriver異常', 'E')
        #     return False
        # lm_wd.command_executor._commands['send_command'] = command
        # lm_wd.execute('send_command', params)

        od_wd = web_driver.driver()
        if od_wd is None:
            com.dialog('WebDriver(音読)で異常が発生しました。', 'WebDriver異常', 'E')
            return False
        od_wd.command_executor._commands['send_command'] = command
        od_wd.execute('send_command', params)
        od_wd.get(cst.ENGLISH_DICT_URL['音読'][1])
        com.sleep(1)
        web_driver.find_element(od_wd, 'id_text').click()
        com.sleep(3)

        shot, gray = com.shot_grab()
        x, y = com.match(shot, gray, cst.MATCH_PATH + 'english/ondoku_text.png', (255, 0, 255))
        com.click_pos(int(x / 2 + 20), int(y / 2 + 100))

        try:
            with open(cst.TEMP_PATH[cst.PC] + 'English/content.js', 'r') as in_file:

                data = in_file.read()
                data = data[data.find('\n') + 1:]
                data = json.loads(data)

                count = 0

                window = com.progress(self.myjob, ['MP3ダウンロード(' + str(len(data)) + ')', len(data)], interrupt=True)
                event, values = window.read(timeout=0)

                for select in selects:
                    lv = int(select.split('_')[1])

                    for i in range(0, len(data[str(lv)])):
                        for key in data[str(lv)][i]:

                            count += 1
                            window['MP3ダウンロード(' + str(len(data)) + ')_'].update(count)

                            for k in range(0, len(MP3_DL)):

                                url = cst.ENGLISH_DICT_URL[MP3_DL[k][0]][1]
                                if '音読' != MP3_DL[k][0]:
                                    url = (data[key] if 0 == len(url) else url % key)

                                if 0 == len(url):
                                    continue

                                name = key + '_' + str(k + 1) + '.mp3'

                                if '音読' == MP3_DL[k][0]:

                                    for m in range(0, MP3_DL[k][1]):

                                        before = os.listdir(MP3_PATH)
                                        name = key + '_' + str(m + 1) + '.mp3'

                                        web_driver.select_click(web_driver.find_element(od_wd, 'id_voice'), m)

                                        com.click_pos(int(x / 2 + 20), int(y / 2 + 100))
                                        web_driver.find_element(od_wd, 'id_text').send_keys(Keys.COMMAND, 'a')
                                        com.clip_copy(key)

                                        web_driver.find_element(od_wd, 'submit').click()
                                        com.sleep(2)
                                        html = od_wd.page_source
                                        html = html[html.find('<source'): ]
                                        html = html[html.find('"') + 1: html.find('type')]
                                        html = html[: html.find('"')]
                                        urllib.request.urlretrieve(html, MP3_PATH + '/' + name)
                                        # web_driver.find_element(od_wd, 'download-button').click()

                                        for sec in range(0, 5):
                                            com.sleep(1)
                                            after = os.listdir(MP3_PATH)
                                            diff_list = set(before) ^ set(after)
                                            if 0 < len(diff_list):
                                                if os.path.exists(MP3_PATH + '/' + name):
                                                    os.remove(MP3_PATH + '/' + name)
                                                os.rename(MP3_PATH + '/' + list(diff_list)[0], MP3_PATH + '/' + name)
                                                break
                                        com.sleep(1)
                                else:
                                    continue
                                # elif 'LONGMAN' == MP3_DL[i][0]:
                                #
                                #     is_html = False
                                #     for _ in range(0, 60):
                                #
                                #         try:
                                #             lm_wd.get(url)
                                #             matching.click_pos(200, 200)
                                #             pgui.hotkey('command', 's')
                                #
                                #             is_html = True
                                #             break
                                #         except:
                                #             wd_error += 1
                                #             try: lm_wd.quit()
                                #             except: pass
                                #             try: lm_wd = web_driver.driver()
                                #             except: pass
                                #
                                #     if not is_html:
                                #         com.log('MP3取得ミス: ' + key, lv='W')
                                #         com.dialog('MP3を取得ミスしました。\n　' + key, title='MP3取得ミス', lv='W')
                                #         return False
                                # else:
                                #     urllib.request.urlretrieve(url, MP3_PATH + name)
        finally:
            # try: lm_wd.quit()
            # except: pass
            try: od_wd.quit()
            except: pass
            try: window.close()
            except: pass

        return True

    # フレーズ集作成、MP3参照辞書作成
    def _create_phrases(self, _):

        merges = dict()
        merges['0'] = []
        mp3_dict = {}
        derivative = {}
        phrase_max = 0

        with open(cst.TEMP_PATH[cst.PC] + 'English/' + FUNCTIONS[6][2] + '.' + FUNCTIONS[6][3], 'r') as in_file:
            in_file = in_file.read().split('\n')
            for row in in_file:

                if 0 == len(row):
                    continue

                cols = row.split(',')

                phrase = cols[1].split(' | ')
                phrases= {phrase[0]: {'meaning': ([''] if 1 == len(phrase) else phrase[1].split(' / ') )}}
                try:
                    merges[cols[0]].append(phrases)
                except:
                    merges[cols[0]] = [phrases]

                phrase_max = cols[0]

        check_dict = {}
        best_dict = {}
        group_dict = {}
        with open(cst.TEMP_PATH[cst.PC] + 'English/content.js', 'r') as in_file:

            data = in_file.read()
            data = data[data.find('\n') + 1:]
            data = json.loads(data)
            mp3_path = cst.TEMP_PATH[cst.PC] + 'English/mp3/'

            for lv in range(1, int(cst.ENGLISH_MASTER_LEVEL / 2) + 1):

                for i in range(0, len(data[str(lv)])):
                    for key in data[str(lv)][i]:
                        lists = []

                        if key in ['May', 'been']:
                            continue

                        # MP3ファイル、枝番付与
                        for k in range(0, len(MP3_DL)):

                            if os.path.exists(mp3_path + key + '.mp3'):
                                os.rename(mp3_path + key + '.mp3', mp3_path + key + '_2.mp3')

                        # MP3参照辞書
                        for k in range(0, len(MP3_DL)):
                            name = key + '_' + str(k + 1) + '.mp3'

                            if os.path.exists(mp3_path + name):
                                lists.append(name)

                        dicts = data[str(lv)][i][key]
                        if '助動詞' in dicts['partspeech']:
                            merges['0'].append(
                                {key:{'meaning': [text for text in dicts['meaning']
                                                  if text not in ['缶', '5月'] and text.find('過去形') < 0],
                                      'changes': [text for text in dicts['changes']
                                                  if text.find('複数形') < 0 and 'shall' != key]
                                      }})

                        else:
                            for k in range(0, len(merges[phrase_max])):
                                for word in merges[phrase_max][k]:

                                    ignores = merges[phrase_max][k][word]['meaning'][0]
                                    if  key == word \
                                            or (1 < len(ignores)
                                                and (key in ignores.split(' ')
                                                or ('un' == word and key.startswith('under'))
                                                or ('re' == word and key.startswith('real'))
                                                or ('for' == word and key.startswith('fore'))
                                                or ('in' == word and key.startswith('inter')))):
                                        continue

                                    is_not_word = True
                                    if word in PHRASE_SUFFIX:

                                        if not key.endswith(word):
                                            continue
                                        is_not_word = False

                                    elif word in ['ever']:
                                        if not key.endswith(word) and not key.startswith(word):
                                            continue
                                        is_not_word = False

                                    else:
                                        if not key.startswith(word):
                                            continue

                                        if 're' == word:
                                            for meaning in dicts['meaning']:

                                                for check in ['再', '複', '続', '応', '反', '改', '帰', '返', '戻', '別', '退']:
                                                    if 0 <= meaning.find(check):
                                                        is_not_word = False
                                                        break

                                                if is_not_word:
                                                    break
                                        else:
                                            is_not_word = False

                                    if is_not_word:
                                        continue

                                    try:
                                        derivative[word].append([key] + [text for text in dicts['meaning']])
                                    except:
                                        derivative[word] = [[key] + [text for text in dicts['meaning']]]

                        for k in range(0, len(dicts['others'])):
                            if 0 <= dicts['others'][k].find('比較'):
                                others = dicts['others'][k].split(', ')
                                for m in range(0, len(others)):
                                    if 0 <= others[m].find('比較'):
                                        targets = others[m].split('(')[0].split(',')
                                        for target in targets:
                                            if key in check_dict:
                                                check_dict[key].append(target)
                                            else:
                                                check_dict[key] = [target]

                        for k in range(0, len(dicts['others'])):
                            if 0 <= dicts['others'][k].find('最上級'):
                                others = dicts['others'][k].split(', ')
                                for m in range(0, len(others)):
                                    if 0 <= others[m].find('最上級'):
                                        targets = others[m].split('(')[0].split(',')
                                        for target in targets:
                                            if target in best_dict:
                                                best_dict[target].append(key)
                                            else:
                                                best_dict[target] = [key]

                        for k in range(0, len(dicts['others'])):
                            if 0 <= dicts['others'][k].find('同義'):
                                others = dicts['others'][k].split(', ')
                                for m in range(0, len(others)):
                                    if 0 <= others[m].find('同義'):
                                        targets = others[m].split('(')[1].replace(')', '').replace(' ', ',').split(',')
                                        for target in targets:
                                            if target == key:
                                                continue
                                            if target in group_dict:
                                                group_dict[target].append(key)
                                            else:
                                                group_dict[target] = [key]

                        mp3_dict[key] = lists
        merges[phrase_max] = []
        for word in derivative:
            derivative[word] = sorted(derivative[word], key=lambda x: x[0])

        for word in derivative:
            for i in range(0, len(derivative[word])):
                merges[phrase_max].append(
                    {word: {'pronounce': derivative[word][i][0], 'meaning': derivative[word][i][1:]}})

        with open(cst.TEMP_PATH[cst.PC] + 'English/Phrase.js', 'w') as out_file:
            out_file.write('const PHRASES =\n' + json.dumps(merges, ensure_ascii=False, indent=4) + '\n')
            out_file.write('const CHECKS =\n' + json.dumps(check_dict, ensure_ascii=False, indent=4) + '\n')
            out_file.write('const BESTS =\n' + json.dumps(best_dict, ensure_ascii=False, indent=4) + '\n')
            out_file.write('const GROUPS =\n' + json.dumps(group_dict, ensure_ascii=False, indent=4) + '\n')

        with open(cst.TEMP_PATH[cst.PC] + 'English/MP3.js', 'w') as out_file:
            out_file.write('const MP3 =\n' + json.dumps(mp3_dict, ensure_ascii=False, indent=4))

        return True

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
