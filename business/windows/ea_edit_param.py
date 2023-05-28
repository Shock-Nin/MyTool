#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

from business. windows import ea_edits as inheritance

import os
import glob
import pandas as pd

PRM_PATH = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH
MQ4_PATH = cst.MT4_DEV[cst.PC] + 'MQL4/Experts/'


class EaEditParam:

    def do(self):

        # .setファイルをCSV化
        is_end = _edit_setfiles()
        if 0 < len(is_end):
            return com.close(is_end)

        # .mq4ファイルをCSV化
        is_end = _edit_mqlfiles()
        if 0 < len(is_end):
            return com.close(is_end)

        # 照合用test.setファイルをCSV化
        is_end = _edit_test_file()
        if 0 < len(is_end):
            return com.close(is_end)

        # .htmファイルをCSV化
        is_end = _edit_htmfiles()
        if 0 < len(is_end):
            return com.close(is_end)

        # CSVファイルからHTML化
        is_end = _output_html()
        if 0 < len(is_end):
            return com.close(is_end)

        return 0


# .setファイルをCSV化
def _edit_setfiles():

    # .setファイル名のリストを取得
    prm_lists = inheritance.prm_list()
    read_files = []
    err_msg = ''

    # リストからファイルの読み込み
    for path in prm_lists:
        files = os.listdir(PRM_PATH + path[0])
        read_file = []

        for file in files:
            try:
                read_file.append(open(PRM_PATH + path[0] + '/' + file, 'r').read())

            except Exception as e:
                err_msg += '\n　' + path[0] + file + '\n　　' + str(e)
                com.log(str(e), 'W')

        read_files.append(read_file)

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    eas = []
    cols = []
    ea_names = []

    # 読み込んだ対象ファイルの整形
    for files in read_files:
        prms = []
        is_col = False

        for file in files:
            col = []
            prm = []

            datas = file.split('\n')
            for data in datas:

                if 0 <= data.find(',') or 0 <= data.find('_____'):
                    continue
                vals = data.split('=')
                col.append(vals[0])

                try:
                    val = vals[1]
                    if 'Comments' == vals[0]:
                        ea_name = val.split('_')[0]
                        val = val.split('_')[1]

                    prm.append(val)
                except:
                    prm.append('')

            if not is_col:
                cols.append(col)

            prms.append(prm)
            is_col = True

        eas.append(prms)
        ea_names.append(ea_name)

    # 整形データの書き出し
    for i in range(0, len(cols)):
        path = cst.DATA_PATH[cst.PC] + 'Set_' + ea_names[i] + '.csv'

        with open(path, 'w') as f:
            f.write(",".join(cols[i])[:-1] + '\n')

            vals = ''
            for prms in eas[i]:
                vals += ",".join(prms)[:-1] + '\n'
            f.write(vals[:-1])

            com.log('ファイル作成: ' + path)

    return []


# .mq4ファイルをCSV化
def _edit_mqlfiles():

    eas = []
    ea_names = []
    err_msg = ''

    files = os.listdir(MQ4_PATH)
    for file in files:
        try:
            # .mq4ファイル以外とサンプルはパス
            if file.find('.mq4') < 0 or file.find('Shocknin') < 0 or 0 <= file.find(' '):
                continue

            is_start = False
            prms = []
            prm = ''

            # mq4ファイルを、UTF-16で読み込み
            ea_names.append(file.replace('.mq4', ''))
            with open(MQ4_PATH + '/' + file, 'r', encoding='utf16') as f:

                datas = f.read().split('\n')
                for i in range(0, len(datas)):

                    # 取得の対象範囲(最初のvoid〜forかelseまで)
                    if 0 <= datas[i].find('void '):
                        is_start = True
                    elif 0 <= datas[i].find('for') or 0 <= datas[i].find('else {'):
                        break
                    if not is_start:
                        continue

                    # 最初のif〜次のifまで
                    if 0 <= datas[i].find('if ('):
                        cur = datas[i][datas[i].find('"') + 1: datas[i].rfind('"')]

                        if 0 <= datas[i].find(';'):
                            prm += datas[i].split(' { ')[1].replace(' ', '').replace(';', ',')
                        i += 1

                        # ifもforもelseもない間、行を進めて取得を続ける
                        while datas[i].find('if (') < 0 and datas[i].find('for') < 0 and datas[i].find('else {') < 0:
                            prm += datas[i].replace(' ', '').replace(';', ',')
                            i += 1

                        prms.append(cur + ',' + prm)
                        prm = ''

            eas.append(prms)

        except Exception as e:
            err_msg += '\n　' + file + '\n　　' + str(e)
            com.log(str(e))

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    # 整形データの書き出し
    for i in range(0, len(eas)):
        path = cst.DATA_PATH[cst.PC] + 'Mql_' + ea_names[i] + '.csv'

        with open(path, 'w') as f:

            for n in range(0, len(eas[i])):
                prm = eas[i][n].split(',')

                if 0 == n:
                    f.write('Comments,' +
                            ",".join([(prm[k].split('[')[0].replace('_', '') + "_0" +
                                       str(int(prm[k].split('=')[0][prm[k].split('=')[0].find('[') + 1:prm[k].split('=')[0].find(']')]) + 1)
                                       if 0 <= prm[k].split('=')[0].find('[') else
                                       prm[k].split('=')[0].replace('_', '')).replace('s_', '_').capitalize()
                                      for k in range(1, len(prm) - 1)]))

                f.write('\n' + prm[0].replace('USD', '') + ',')
                f.write(",".join([prm[k].split('=')[1] for k in range(1, len(prm) - 1)]))

            com.log('ファイル作成: ' + path)
    return []


# 照合用test.setファイルをCSV化
def _edit_test_file():

    file = PRM_PATH + 'test.set'
    try:
        with open(file, 'r') as infile:
            datas = infile.read().split('\n')

            with open(cst.DATA_PATH[cst.PC] + 'TestSet.csv', 'w') as outfile:

                col = ''
                prm = ''

                for data in datas:

                    if 0 <= data.find(',') or 0 <= data.find('_____'):
                        continue
                    vals = data.split('=')
                    col += vals[0] + ','
                    prm += (vals[1] if 1 < len(vals) else '') + ','

                outfile.write(col[:-2] + '\n')
                outfile.write(prm[:-2])

        com.log('ファイル作成: ' + cst.DATA_PATH[cst.PC] + 'TestSet.csv')

    except Exception as e:
        com.log(str(e))
        return ['以下のファイルでエラーが発生しました。\n' + file, '読み込みエラー', 'E']

    return []


# .htmファイルをCSV化
def _edit_htmfiles():
    ea_name = 'WheSitDoch'

    # .htmファイル名のリストを取得
    htm_lists = glob.glob(cst.MT4_DEV[cst.PC] + 'MQL4/Files/' + ea_name + '/Test_*/*.htm')
    read_files = []
    err_msg = ''

    # htmファイルの読み込み
    tf = ['M5', 'M15', 'M30', 'H1']
    for i in range(0, len(tf)):
        cur_file = []

        for k in range(0, len(cst.CURRENCIES_EA[0])):
            trade_file = []

            for file in htm_lists:
                if file.find('_' + tf[i] + '_') < 0:
                    continue
                if ('GOLD' != cst.CURRENCIES_EA[0][k] and file.find(cst.CURRENCIES_EA[0][k]) < 0) \
                        or ('GOLD' == cst.CURRENCIES_EA[0][k] and file.find('XAU') < 0):
                    continue
                try:
                    trade_file.append(open(file, 'r', encoding='utf16').read())

                except Exception as e:
                    err_msg += '\n　' + file + '\n　　' + str(e)
                    com.log(str(e), 'W')

            if 0 < len(trade_file):
                cur_file.append(trade_file)

        if 0 < len(cur_file):
            read_files.append(cur_file)

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    logic_no = 0
    prm = {}
    result = {tf[i]: {} for i in range(0, len(tf))}
    for i in range(0, len(tf)):

        for k in range(0, len(cst.CURRENCIES_EA[0])):
            cur_data = {}

            for m in range(0, len(read_files)):
                for n in range(0, len(read_files[m])):
                    data = {}

                    for p in range(0, len(read_files[m][n])):

                        html = read_files[m][n][p]
                        title = html[html.find('<title>'):]
                        title = title[title.find('>') + 1: title.find(' :')]
                        title = title.split('_')

                        if tf[i] != title[1]:
                            continue

                        if ('GOLD' != cst.CURRENCIES_EA[0][k] and title[0].find(cst.CURRENCIES_EA[0][k]) < 0) \
                                or ('GOLD' == cst.CURRENCIES_EA[0][k] and title[0].find('XAU') < 0):
                            continue

                        html = html[html.find('パラメーター'):]
                        html = html[html.find('title'):]
                        html = html[html.find('"') + 1: html.find('">')]
                        html = html.split('; ')[:-1]

                        if 0 == logic_no:
                            for q in range(-2, 3):
                                if 0 == q:
                                    continue

                                for r in range(1, len(html)):
                                    prm['[' + ('+' if 0 < q else '') + str(q) + ']' + html[r].split('=')[0]] = ''
                        if data is None:
                            data = prm

                        logic_no = html[0].split('=')[1]
                        logic_no = ('+' if 0 < int(logic_no) else '') + str(logic_no)

                        for r in range(1, len(html)):
                            prms = html[r].split('=')
                            data['[' + logic_no + ']' + str(prms[0])] = str(prms[1])

                        cur_data = data

                    if 0 < len(cur_data):
                        result[title[1]][title[0]] = cur_data
                        break


    # 整形データの書き出し
    path = cst.DATA_PATH[cst.PC] + 'Set_' + ea_name + '.csv'
    with open(path, 'w') as f:
        f.write('TimeFrame,Currency,' + ",".join(key for key in prm) + '\n')

        for tf in result:
            for cur in result[tf]:
                vals = ''

                for key in prm:
                    try:
                        vals += ',' + result[tf][cur][key]
                    except:
                        vals += ', '

                f.write(tf +','+ cur + vals + '\n')

    com.log('ファイル作成: ' + path)
    return []


# CSVファイルからHTML化
def _output_html():

    read_sets = []
    read_mqls = []

    # 作成したCSVを全て、種類分けしながら読み込む
    files = os.listdir(cst.DATA_PATH[cst.PC])
    for file in files:
        try:
            if 0 <= file.find('Set_'):
                read_sets.append([file, pd.read_csv(cst.DATA_PATH[cst.PC] + file)])
            elif 0 <= file.find('Mql_'):
                read_mqls.append([file, pd.read_csv(cst.DATA_PATH[cst.PC] + file)])
            elif 0 <= file.find('Test'):
                read_set = pd.read_csv(cst.DATA_PATH[cst.PC] + file)

        except Exception as e:
            com.log(str(e))
            return ['以下のファイルでエラーが発生しました。' + file, '読み込みエラー', 'E']

    for i in range(0, len(read_sets)):
        ea = read_sets[i]
        ea_name = ea[0].split('_')[1].replace('.csv', '')

        # HTMLヘッダー
        html = '<html><head><title>' + ea_name + '</title>'
        html += '<meta charset="utf-8"/></head><body><div align="center">'
        html += '<table><tr><td class="eaName" align="center">' + ea_name + '</td></tr><tr><td>'
        html += '<table cellspacing="0" cellpadding="0"><tr><td>'

        prms = pd.DataFrame.transpose(ea[1])
        mqls = pd.DataFrame.transpose(read_mqls[i][1])
        set_cur = ''

        if 'WheSitDoch' != ea_name:
            continue

        set_html = ''
        prm_html = ''
        total = 1

        for key in prms.index:

            if 'WheSitDoch' == ea_name:
                prm_html = ''
                time_frame = ''
                count = -1

                # パラメータ
                for prm in prms:

                    if 'TimeFrame' != key:
                        continue
                    count += 1
                    total += 1

                    if 0 < len(time_frame) and time_frame != str(prms[prm][key]):
                        prm_html += '<td class="prm" align="center"'
                        prm_html += ' colspan="' + str(count) + '">' + time_frame + '</td>'
                        count = 0

                    time_frame = str(prms[prm][key])

                if 'TimeFrame' == key:
                    prm_html += '<td class="prm" align="center"'
                    prm_html += ' colspan="' + str(count + 1) + '">' + time_frame + '</td>'

                for prm in prms:
                    if 'TimeFrame' == key:
                        continue

                    prm_html += '<td class="prm'  + (' zero' if 0 == len(str(prms[prm][key]).strip()) else '')
                    prm_html += '" align="'  + ('center' if 'Currency' == key else 'right')
                    prm_html += '">' + str(prms[prm][key]) + '</td>'

                if 0 <= key.find('Currency') or 0 <= key.find('OpenWait'):
                    prm_html += '<tr><td bgcolor="#CCCCCC" height="5" colspan="' + str(total) + '"></td></tr>'

                html += '<tr><td class="col'
                html += '" align="left">' + key + '</td>' + prm_html.replace('USD', '').replace('XAU', 'GOLD') + '</tr>'
            else:
                # test.setは、「Comments」に含まれるEA名と通貨を分割
                if 'Comments' == key:
                    val = read_set[key].item()

                    if val.split('_')[0] == ea_name:
                        set_cur = val.split('_')[1]

                # 表示させないパラメータ項目
                if 0 <= key.find('Logic') or key in ['TradeMargin', 'Positions', 'Safety']:
                    continue

                # パラメータ
                for k in range(0, len(prms)):

                    # .setのパラメータは、0値をグレーアウト
                    zero = ''
                    try: zero = (' zero' if 0 == float(prms[k][key]) else '')
                    except: pass

                    try:
                        # test.setのパラメータ、.setとパラメータが相違の場合は黄枠表示
                        if 0 < len(set_cur) and set_cur == prms[k]['Comments']:
                            item = str(read_set[key].item())
                            set_html += '<td class="prm' + ('' if str(prms[k][key]) == item else ' ng_set') + \
                                        (' up_line' if 0 <= key.find('Lot') or key in ['Trend4H'] else '') + \
                                        '" align="' + ('center">' + set_cur if 'Comments' == key else 'right">' + item) + '</td>'

                        ng_mql = ''
                        for n in range(0, len(mqls)):
                            if prms[k]['Comments'] != mqls[n]['Comments']:
                                continue

                            # .mq4と.setのパラメータを照合、相違の場合は赤枠表示
                            for mql_key in mqls.index:
                                if key == mql_key:
                                    ng_mql = ('' if mqls[n][mql_key] == prms[k][key] else ' ng_mql')

                            # .setのパラメータ
                            prm_html += '<td class="prm' + zero + ng_mql + \
                                        (' up_line' if 0 <= key.find('Lot') or key in ['Trend4H'] else '') + \
                                        '" align="' + ('center' if 'Comments' == key else 'right') + \
                                        '">' + str(prms[k][key]) + '</td>'
                    except: pass

                html += '<tr>' + set_html + '<td class="col'
                html += (' up_line' if 0 <= key.find('Lot') or key in ['Trend4H'] else '')
                html += '" align="left">' + key + '</td>' + prm_html + '</tr>'

        # HTMLフッター(スタイル)
        html += '</table></td></tr></table></div><style type="text/css">'
        html += '.eaName   {padding: 10px; background: #FFCCFF; font-size: 24px;}'
        html += '.row      {border: 1px solid #DDDDDD; padding: 5px 15px; background: #CCCCFF;}'
        html += '.col      {border: 1px solid #DDDDDD; padding: 5px 15px; background: #CCFFFF;}'
        html += '.prm      {border: 1px solid #DDDDDD; padding: 5px 10px;}'
        html += '.zero     {background: #EEEEEE; color: #AAAAAA;}'
        html += '.ng_set   {background: #FFFF55; color: #000000;}'
        html += '.ng_mql   {background: #FF0000; color: #FFFFFF;}'
        html += '.up_line  {border-top: 2px solid #000000;}'
        html += '</style></body></html>'

        path = cst.DATA_PATH[cst.PC] + ea_name + '.html'
        with open(path, 'w', encoding='utf8') as f:
            f.write(html)
        com.log('ファイル作成: ' + path)

    return []
