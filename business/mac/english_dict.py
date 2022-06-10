#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

from common import web_driver

import re
import json
import pykakasi
import pandas as pd
import PySimpleGUI as sg
import pyautogui as pgui
import pyperclip
import urllib.parse

IS_HEADLESS = True

FUNCTIONS = [
    ['基本マスタ', '_create_master', 'Master', 'csv'],
    ['Weblio', '_get_weblio', 'Weblio', 'json'],
    ['英ナビ', '_get_Einavi', 'Einavi', 'json'],
    ['Google', '_get_google', 'Google', 'json'],
    ['イメージ', '_get_images', 'Image', 'json'],
    ['辞書', '_merge_content', 'Content', 'json']
]


class EnglishDict:

    def __init__(self, job):
        self.myjob = job

    def do(self):
        layout = [[FUNCTIONS[i][0] + '_' + str(k) if i in [0, 1, 2, 3, 4] else None
                   for k in range(1, cst.ENGLISH_MASTER_LEVEL + 1)] +
                  [FUNCTIONS[i][0] + '_追加' if i in [1, 2, 3] else None] +
                  [FUNCTIONS[i][0] + '_マージ' if i in [0, 4, 5] else None]
                  for i in range(0, len(FUNCTIONS))]

        selects = com.dialog_cols('不要なものは外してください。', layout,
                                  ['l' for _ in range(0, len(FUNCTIONS))], '工程選択', obj='check')
        if 0 == len(selects):
            return
        total_time = 0

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

                with open(cst.TEMP_PATH[cst.PC] + 'English/Master_' + str(lv) + '.csv', 'w', encoding='utf8') as outfile:
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
                                wd.get(cst.ENGLISH_DICT_URL['Weblio'] % target)
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
                                       title='TML取得ミス', lv='W')
                            return False

                        # 発音表記
                        if 0 <= html.find('phoneticEjjeDesc'):
                            pronounce = html[html.find('phoneticEjjeDesc'):]
                            pronounce = pronounce[: pronounce.find('phoneticEjjeDc')]
                        else:
                            pronounce = html[html.find('syllableEjje'):]
                            pronounce = pronounce[:pronounce.find('</div>')]

                        pronounce = pronounce[pronounce.find('>') + 1: pronounce.rfind('</span>')]
                        while 0 <= pronounce.find('<'):
                            pronounce = pronounce.replace(pronounce[pronounce.find('<'): pronounce.find('>') + 1], '').strip()

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
                                wd.get(cst.ENGLISH_DICT_URL['英ナビ'] % target)
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
                                       title='TML取得ミス', lv='W')
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

                        word[target] = {
                            'pronounce': pronounce, 'meaning': meaning, 'partspeech': partspeeches,
                            'changes': changes, 'examples': examples, 'others': others}
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

                words = []
                total_times = 0
                count = 0
                ng_target = ''

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
                                wd.get(cst.ENGLISH_DICT_URL['Google'] % target)
                                com.sleep(1)

                                while sec < 5:

                                    shot, gray = com.shot_grab()
                                    x, y = com.match(shot, gray, cst.MATCH_PATH + 'english/google_trans.png', (0, 0, 255))

                                    if x is None:
                                        com.sleep(1)
                                        sec += 1
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
                                sec += 1

                        if not is_match:
                            com.log('マッチングエラー: Lv' + str(lv) + ' - ' + str(count + 1) + ' ' + target, lv='W')
                            ng_target += str(lv) + ',' + target + '\n'
                            count += 1
                            continue

                        pos_x, pos_y = pgui.position()
                        pgui.click(int(x / 2 - 100), int(y / 2 + 20), clicks=2, interval=0, button='left')

                        com.sleep(1)
                        pgui.hotkey('command', 'a')
                        pgui.hotkey('command', 'c')
                        com.sleep(1)

                        com.move_pos(pos_x, pos_y)
                        data = pyperclip.paste().split('help_outline')

                        pronounce = data[0].split('/')[0].split('\n')
                        pronounce = pronounce[len(pronounce) - 2]

                        meanings = []
                        partspeeches = []

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

                if 0 < len(words):
                    insert_datas.append(words)
                else:
                    insert_datas.append('')

                com.log('Google(' + com.conv_time_str(total_times) + '): Lv' + str(lv))
                window.close()

                if not insert:
                    with open(cst.TEMP_PATH[cst.PC] + 'English/dict/Google_' + str(lv) + '.json', 'w') as out_file:
                        json.dump({lv: words}, out_file, ensure_ascii=False, indent=4)

                    if 0 < len(ng_target):
                        with open(cst.TEMP_PATH[cst.PC] + 'English/Google.csv', 'a') as out_file:
                            out_file.write(ng_target)

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

        out_counts = [0 for _ in range(0, int(cst.ENGLISH_MASTER_LEVEL / 2))]

        plus = {}
        for lv in range(0, cst.ENGLISH_MASTER_LEVEL + 1):
            file = pd.read_json(plus_file.replace(
                FUNCTIONS[1][2] + '.', FUNCTIONS[1][2] + '_' + str(lv) + '.'), encoding='utf8')

            for col in file:
                for i in range(0, len(file[col])):
                    for key in file[col][i]:
                        plus[key] = file[col][i][key]

        google = {}
        for lv in range(0, cst.ENGLISH_MASTER_LEVEL + 1):
            file = pd.read_json(google_file.replace(
                FUNCTIONS[3][2] + '.', FUNCTIONS[3][2] + '_' + str(lv) + '.'), encoding='utf8')

            for col in file:
                for i in range(0, len(file[col])):
                    for key in file[col][i]:
                        google[key] = file[col][i][key]

        insert_file = open(base_file.replace(
            FUNCTIONS[2][2] + '.', FUNCTIONS[2][2] + '_0.'), 'r', encoding='utf8').read()
        insert_file = json.loads(insert_file)

        rows = []
        merge = []
        merges = {}

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
                            except: pass

                            new_datas.append({key2: data[key2]})
                            is_append = True
                            break

                    if is_append:
                        break

                merges[lv] = new_datas

            rows = []

            for words in merges[lv]:
                word = {}

                for key in words:

                    if len(key) < 2:
                        continue

                    # 発音表記がGoogleにあった場合、優先使用
                    try:
                        if re.match(r'\ˈ', google[key]['pronounce']) \
                                or re.match(r'([a-z])', google[key]['pronounce']) \
                                or re.match(r'([A-Z])', google[key]['pronounce']):
                            words[key]['pronounce'] = google[key]['pronounce']
                    except: pass

                    # 発音表記がない場合、Weblio使用
                    if 0 == len(words[key]['pronounce']):
                        words[key]['pronounce'] = plus[key]['pronounce']

                    words[key]['pronounce'] = words[key]['pronounce'].replace('&nbsp;', ' ')

                    # 品詞がある場合は編集
                    if 0 < len(words[key]['partspeech']):
                        texts = words[key]['meaning'].replace('（', '(').replace('）', ')')
                        texts = texts.replace('，', '、').split('、')
                        meanings = []

                        for text in texts:
                            meanings.append(text)

                        words[key]['meaning'] = list(set(meanings))[1:]

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
                    if (0 <= meaning.find('の')
                            and (0 <= meaning.find('分詞') or 0 <= meaning.find('過去形')
                                 or 0 <= meaning.find('人称単数現在') or 0 <= meaning.find('複数形'))):

                        com.log('変化形(meanibg)除外: ' + str(lv) + ', ' + key + ' | ' + meaning)
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

                            if 0 <= txt.find(check):
                                txt = txt.replace(check, '[' + check[1: -1] + ']')

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
                                    or meaning[k].replace(meaning[k][meaning[k].find('['): meaning[k].rfind(']')], '') == \
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
                            meanings.append(text)

                    words[key]['meaning'] = list(set(meanings))

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
                                txt = txt.split(',')[1].strip()

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
                            eng = eng.replace('＝', ' / ').replace('；', ' / ').replace('()', '')
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
                                if texts[0].replace('.', '').replace(',', '').replace(';', '').replace(':', '').lower() == \
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
                            text = list(set([other.strip() for other in text.split(',')]))
                            others.append(other1.split('(')[0] + '(' + ", ".join([other for other in text]) + ')')

                        words[key]['others'] = others

                    # 最終チェック
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

                    texts = words[key]['meaning']
                    meanings = []
                    count = 0

                    for text in texts:

                        if not (text.find(')') < 0 <= text.find('(')
                                or text.find('(') < 0 <= text.find(')')):

                            text = text.replace('．', '、').strip()
                            meanings.append(text)

                            if not re.match(r'([ア-ン])', text):
                                count += 1

                    texts = meanings
                    if 1 <= count:
                        meanings = []

                        for text in texts:
                            if not re.match(r'([ア-ン])', text):
                                meanings.append(text)

                    texts = meanings
                    if 2 < len(texts):

                        meanings = []
                        for i in reversed(range(1, len(texts))):

                            is_meaning = True
                            if 1 < len(texts[i]):
                                for k in range(0, i - 1):

                                    if 1 < len(texts[k]):
                                        if texts[k].startswith(texts[i]) or texts[k].endswith(texts[i]):
                                            is_meaning = False

                                        if (5 < len(texts) and 10 < len(texts[i])) \
                                                or (2 < len(texts) and 13 < len(texts[i])):
                                            is_meaning = False

                            if is_meaning:
                                meanings.append(texts[i])

                    meanings = list(set(meanings))
                    words[key]['meaning'] = meanings

                    # 例外処理
                    reg_key = key
                    if 'TRUE' == key:
                        reg_key = key.lower()

                    # 単語に格納
                    if 0 < len(words[key]['partspeech'][0]):
                        word[reg_key] = words[key]
                    else:
                        com.log('partspeechなし: ' + str(lv) + ', ' + key)
                        out_counts[lv - 1] += 1

                if 0 < len(word):
                    rows.append(word)

            merges[lv] = rows

        with open(cst.TEMP_PATH[cst.PC] + 'English/Content.js', 'w') as out_file:
            out_file.write('const CONTENTS =\n' + json.dumps(merges, ensure_ascii=False, indent=4))

        com.log('除外件数: ' + str([str(i + 1) + '(' + str(out_counts[i]) + ')'
                                for i in range(0, len(out_counts))]))
        return True

    def _get_images(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd_error = 0
        is_merge = False

        try:
            for select in selects:

                if 0 <= select.find('マージ'):
                    is_merge = True
                    continue

                lv = int(select.split('_')[1])

                wd.get(urllib.parse.quote(cst.ENGLISH_IMAGES_URL, 'utf8'))
                com.sleep(5)

                target = ''

        except Exception as e:
            com.log(self.myjob + ' イメージ作成 エラー発生: [Lv' + str(lv) + ', ' + target + '] ' + str(e), lv='W')
            com.dialog(self.myjob + ' イメージ作成 でエラーが発生しました。\n[Lv' +
                       str(lv) + ', ' + target + ']\n' + str(e), title='エラー発生', lv='W')
            return False

        # finally:
        #     try: window.close()
        #     except: pass
        #     try: wd.quit()
        #     except: pass

        # マージを実行する場合
        if is_merge:
            self._merge_content(3)

        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
