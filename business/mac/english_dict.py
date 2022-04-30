#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

from common import web_driver

import ast
import json
import pandas as pd
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

    def _get_contents(self, selects, insert=None):

        wd = web_driver.driver(headless=IS_HEADLESS)
        if wd is None:
            com.dialog('WebDriverで異常が発生しました。', 'WebDriver異常', 'E')
            return False

        wd_error = 0
        is_merge = False

        try:
            datas = open(cst.TEMP_PATH[cst.PC] + 'English/' +
                         ('Master' if insert is None else 'Insert') + '.csv', 'r').read().split('\n')

            for select in selects:

                if 0 <= select.find('マージ'):
                    is_merge = True
                    continue

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

                    # # 部分検証用
                    # if count < 260:
                    #     count += 1
                    #     continue
                    # if 265 < count:
                    #     break

                    # 単語個別のHTML取得を、1分まで実施
                    for target in targets:
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
                                eng = eng.replace('（を略して通例）', ' ')

                                jpn = txt[txt.find('<p') + 1:]
                                jpn = jpn[jpn.find('<p') + 1:]
                                jpn = jpn[jpn.find('>') + 1:]

                                jpn = (jpn.split('(')[0].strip() if 0 <= jpn.find('<b>') else jpn)
                                jpn = (jpn if jpn.find('「') < 0 <= jpn.find('」') else jpn.replace('」', ''))
                                jpn = (jpn if jpn.find('」') < 0 <= jpn.find('「') else jpn.replace('」', ''))

                                examples.append(eng + ' | ' + jpn)

                        up_name = target[:1].upper() + target[1:]
                        target = (up_name if 0 <= html.find('title="' + up_name + '"') else target)
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
                        com.log('Content(' + com.conv_time_str(run_time) + '): Lv' +
                                str(lv) + ', ' + target + '(' + str(count) + ')')

                com.log('Content(' + com.conv_time_str(total_times) + '): Lv' + str(lv))
                window.close()

                if insert is None:
                    with open(cst.TEMP_PATH[cst.PC] + 'English/Content_' + str(lv) + '.json', 'w') as out_file:
                        json.dump({lv: words}, out_file, ensure_ascii=False, indent=4)
                else:
                    return words

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

        merge_file = cst.TEMP_PATH[cst.PC] + 'English/' + FUNCTIONS[fnc][2] + '.' + FUNCTIONS[fnc][3]

        # Master.csv作成
        if 0 == fnc:
            datas = []

            for lv in range(1, cst.ENGLISH_MASTER_LEVEL + 1):
                data = pd.read_csv(merge_file.replace(
                    FUNCTIONS[fnc][2] + '.', FUNCTIONS[fnc][2] + '_' + str(lv) + '.'), header=None)

                data = data.drop(data.columns[[2, 3]], axis=1)
                rows = []

                for i in range(0, len(data)):
                    phrase = data.at[i, 1]

                    if 0 <= phrase.find(' '):
                        phrase = phrase.split(' ')

                    elif 0 <= phrase.find('-'):
                        phrase = phrase.split('-')
                    else:
                        phrase = [phrase]

                    for txt in phrase:
                        rows.append(txt.lower())

                rows.sort()
                datas.append(pd.DataFrame(data=[[str(lv), row] for row in rows]))

            datas = pd.concat(datas)
            datas = datas.drop_duplicates(datas.columns[[1]]).copy()

            datas.to_csv(merge_file, header=False, index=False)

        # Content.json作成
        if 1 == fnc:

            inserts = self._get_contents({'インサート_1': True}, insert=True)

            out_count = 0
            merges = {}

            for lv in range(1, cst.ENGLISH_MASTER_LEVEL + 1):
                merge = pd.read_json(merge_file.replace(
                            FUNCTIONS[fnc][2] + '.', FUNCTIONS[fnc][2] + '_' + str(lv) + '.'), encoding='utf8')

                if 1 == lv:
                    datas = pd.DataFrame(pd.Series(inserts), columns=[1])
                    old_keys = []
                    new_keys = []
                    old_datas = []
                    new_datas = []

                    for words in merge[lv]:
                        for key in words:
                            old_keys.append(key)
                            new_keys.append(key.lower())
                            old_datas.append({key: words[key]})

                    for i in datas:
                        for data in datas[i]:
                            for key in data:
                                old_keys.append(key)
                                new_keys.append(key.lower())
                                old_datas.append({key: data[key]})

                    new_keys.sort()
                    for key1 in new_keys:
                        is_append = False
                        for data in old_datas:
                            for key2 in data:
                                if key1 == key2.lower():
                                    new_datas.append({key1 if key1 in old_keys else key2: data[key2]})
                                    is_append = True
                                    break
                            if is_append:
                                break

                    merge = {lv: new_datas}

                rows = []
                for words in merge[lv]:

                    word = {}
                    for key in words:

                        if 0 == len(words[key]['pronounce']):
                            com.log('発声なし(pronounce)除外: ' + str(lv) + ', ' + key)
                            out_count += 1
                            continue

                        if 0 == len(words[key]['partspeech']):
                            com.log('品詞なし(partspeech)除外: ' + str(lv) + ', ' + key)
                            out_count += 1
                            continue

                        meaning = words[key]['meaning'].split('、')[0]
                        if 0 <= meaning.find('；') \
                                or (0 <= meaning.find('の')
                                    and (0 <= meaning.find('過去') or 0 <= meaning.find('複数形'))):
                            com.log('変化形(meanibg)除外: ' + str(lv) + ', ' + key + ' | ' + meaning)
                            out_count += 1
                            continue

                        # 意味の編集
                        meaning = words[key]['meaning']
                        if 0 <= meaning.find('対訳は、'):
                            meaning = meaning.split('対訳は、')[1]

                        meanings = []
                        for txt in meaning.split('、'):

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

                        meaning = meaning.replace('{', '(').replace('}', ')')
                        words[key]['meaning'] = meaning.split('、')

                        partspeechs = []
                        txts = []
                        for txt in words[key]['partspeech']:

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
                                partspeechs.append(txt)

                        for txt in txts:
                            if 0 <= txt.find('動詞(') and 2 == v_count:
                                partspeechs.append('動詞(自・他)')
                            elif 0 <= txt.find('名詞(') and 2 == n_count:
                                partspeechs.append('名詞(可算・不可算)')
                            elif 0 <= txt.find('可算名詞(不可算)') or 0 <= txt.find('不可算名詞(可算)'):
                                partspeechs.append('名詞(可算・不可算)')
                            else:
                                partspeechs.append(txt)

                        # 品詞の重複を削除
                        words[key]['partspeech'] = list(set(partspeechs))

                        # 品詞の「動詞」「名詞」を編集
                        partspeechs = []
                        for txt in words[key]['partspeech']:
                            is_txt = True

                            if txt in ['動詞', '名詞']:
                                is_txt = True

                                for txt2 in words[key]['partspeech']:
                                    if txt != txt2 and txt2.startswith(txt):
                                        is_txt = False
                            if is_txt:
                                partspeechs.append(txt)
                        words[key]['partspeech'] = partspeechs

                        # 変化形の「●詞：」を除去
                        changes = []
                        for txt in words[key]['changes']:
                            if 0 <= txt.find(','):
                                txt = txt.split(',')[1].strip()

                            changes.append(txt.split('：')[1] if 0 <= txt.find('：') else txt)
                        words[key]['changes'] = changes

                        word[key] = words[key]
                    if 0 < len(word):
                        rows.append(word)
                merges[lv] = rows

            with open(merge_file.replace('.json', '.js'), 'w') as out_file:
                out_file.write('const CONTENTS =\n' + json.dumps(merges, ensure_ascii=False, indent=4))

                # json.dump(merges, out_file, ensure_ascii=False, indent=4)

        com.log('除外件数: ' + str(out_count))
        return True


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
