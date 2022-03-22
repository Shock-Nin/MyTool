#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

from common import web_driver

import json
import PySimpleGUI as sg
import urllib.parse

IS_HEADLESS = True

FUNCTIONS = [
    ['基本マスタ', '_create_master', 'Master', 'csv'],
    ['コンテンツ', '_get_contents', 'Content', 'json'],
    ['イメージ', '_get_images', 'Image', 'json']
]


class EnglishDict:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        selects = com.dialog_cols('不要なものは外してください。',
                                  [[FUNCTIONS[i][0] + '_' + str(k) for k in range(1, cst.ENGLISH_MASTER_LEVEL + 1)] +
                                   [FUNCTIONS[i][0] + '_マージ'] for i in range(0, len(FUNCTIONS))],
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

    def _create_master(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd.implicitly_wait(3)
        wd_error = 0
        is_merge = False

        try:
            # 4段階のレベル単位で、約2000語のループ
            for select in selects:

                if 0 <= select.find('マージ'):
                    is_merge = True
                    continue

                lv = int(select.split('_')[1])

                index = 1
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
                                            ' - ' + str(index) + ' [' + str(i + 1) + ', wd' + str(wd_error) + ']')
                        window['lv_'].update(lv - 1)

                        try:
                            wd.get(cst.ENGLISH_MASTER_URL + str(lv) + '/' + str(index))
                            html = wd.page_source
                            html = html[html.find('を表示しています'): html.find('掲載しています。')]
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
                        com.log('HTML取得ミス: Lv' + str(lv) + ' - ' + str(index), lv='W')
                        com.dialog('HTMLを取得ミスしました。\n　Lv' + str(lv) + ' - ' + str(index),
                                   title='TML取得ミス', lv='W')
                        return False

                    html = html[html.find('</table'): html.rfind('<div')]
                    html = html[html.find('</tr'): html.rfind('<td ')]

                    # 全体でimgタグがない場合は不在ページ、ループを抜けて次レベルへ
                    if html.find('<img') < 0:
                        break

                    html = html[html.find('<tr>') + 4:].replace('\n', '').split('<hr>')
                    for row in html:

                        # imgタグ(品詞)がなくなったら、ループを抜けて次50語リストへ
                        if row.find('<img') < 0:
                            break

                        row = row[row.find('<a '): row.rfind('</tr>')]
                        row = row[row.find('>') + 1: row.rfind('</td>')]

                        word = row[: row.find('</a>')]
                        img = row[row.find('<img '): row.find('.gif')]
                        img = img[img.rfind('/') + 1:]
                        jpn = row[row.rfind('>') + 1:]

                        words.append(str(lv) + ',' + word + ',' + cst.ENGLISH_NOUNS[img] + ',' + jpn)

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
            self._merge_file(0)

        return True

    def _get_contents(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd.implicitly_wait(3)
        wd_error = 0
        is_merge = False

        try:
            for select in selects:

                if 0 <= select.find('マージ'):
                    is_merge = True
                    continue

                lv = int(select.split('_')[1])
                words = {}

                total_times = 0
                count = 0

                with open(cst.TEMP_PATH[cst.PC] + 'English/Master_' + str(lv) + '.csv', 'r') as read_file:

                    rows = read_file.read().split('\n')[:-1]
                    window = com.progress(self.myjob, ['lv', cst.ENGLISH_MASTER_LEVEL],
                                          ['target', len(rows)], interrupt=True)
                    event, values = window.read(timeout=0)

                    for row in rows:

                        cols = row.split(',')
                        target = cols[1]
                        start_time = com.time_start()

                        # 単語個別のHTML取得を、1分まで実施
                        is_html = False
                        for i in range(0, 60):

                            # 中断イベント
                            if _is_interrupt(window, event):
                                return None

                            window['lv'].update('Lv ' + str(lv) + '/' + str(cst.ENGLISH_MASTER_LEVEL) +
                                                ' [' + str(i + 1) + ', wd' + str(wd_error) + ']')
                            window['lv_'].update(lv - 1)
                            window['target'].update(target + ' ' + str(count + 1) + '/' + str(len(rows)))
                            window['target_'].update(count)

                            try:
                                wd.get(cst.ENGLISH_CONTENTS_URL % target)
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
                        pronounce = html[html.find('phoneticEjjeDesc'):]
                        pronounce = pronounce[:pronounce.find('</span>')]
                        pronounce = pronounce[pronounce.find('>') + 1:]

                        # 変化形
                        change_col = html[html.find('変形一覧'): html.find('学習レベル')]
                        change_col = change_col[change_col.find('<table'): change_col.rfind('</table>')]
                        change_col = change_col[: change_col.rfind('</span>')]
                        change_col = change_col[change_col.find('：'):]
                        change_col = change_col[change_col.find('<td '):]
                        change_col = change_col[change_col.find('>'):].split('</span>')

                        changes = []
                        for col in change_col:
                            if 0 <= col.find('<a '):
                                col = col[col.find('<a '):]
                                col = col[col.find('>') + 1:].replace('</a><span>', '').strip()
                            else:
                                col = col[col.find('>') + 1:].replace('<span>', '').strip()
                            changes.append(col)

                        # 意味・対訳
                        meaning = html[html.find('>') + 1: html.find('</div>')]
                        meaning = meaning[meaning.find('>') + 1: meaning.rfind('</span>')].strip()

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

                                eng = txt[txt.find('<p'): txt.find('>発音を聞く')]
                                eng = eng[eng.find('>') + 1: eng.rfind('<')]
                                eng = eng.replace('<b>', '').replace('</b>', '').replace('</a>', '')
                                eng = eng.split('<span')[0]

                                for k in range(50):
                                    if eng.find('<a ') < 0:
                                        break
                                    eng = eng.replace(eng[eng.find('<a '): eng.find('>') + 1], '')

                                jpn = txt[txt.rfind('>') + 1:]
                                examples.append(eng + ' | ' + jpn)

                        words[target] = {
                            'lv': lv, 'pronounce': pronounce, 'phrase': cols[2] + ' | ' + cols[3],
                            'changes': changes, 'meaning': meaning, 'examples': examples}

                        # 中断イベント
                        if _is_interrupt(window, event):
                            return None

                        count += 1
                        run_time = com.time_end(start_time)
                        total_times += run_time

                        com.log('Content(' + com.conv_time_str(run_time) + '): Lv' +
                                str(lv) + ', ' + target + '(' + str(count) + ')')

                    com.log('Content(' + com.conv_time_str(total_times) + '): Lv' + str(lv))
                    window.close()

                with open(cst.TEMP_PATH[cst.PC] + 'English/Content_' + str(lv) + '.json', 'w') as out_file:
                    json.dump({'word': words}, out_file, ensure_ascii=False, indent=4)

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

        # マージを実行する場合
        if is_merge:
            self._merge_file(1)

        return True

    def _get_images(self, selects):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd.implicitly_wait(3)
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
            self._merge_file(2)

        return True

    def _merge_file(self, fnc):

        with open(cst.TEMP_PATH[cst.PC] + 'English/' + FUNCTIONS[fnc][2] + '.' + FUNCTIONS[fnc][3],
                  'w', encoding='utf8') as merge:
            for i in range(1, cst.ENGLISH_MASTER_LEVEL + 1):

                with open(cst.TEMP_PATH[cst.PC] + 'English/' + FUNCTIONS[fnc][2] + '_' +
                          str(i) + '.' + FUNCTIONS[fnc][3], 'r', encoding='utf8') as file:
                    merge.write(file.read())
        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
