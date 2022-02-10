#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from common import com
from const import cst

import pandas as pd

PRM_PATHS = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATHS
MQ4_PATH = cst.MT4_DEV[cst.PC] + '/MQL4/Experts'


class EaEditParam:

    def __init__(self):
        pass

    def do(self):

        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        # .setファイルをCSV化
        is_end = _edit_setfiles()
        if 0 < len(is_end):
            return is_end

        # .mq4ファイルをCSV化
        is_end = _edit_mqlfiles()
        if 0 < len(is_end):
            return is_end

        # 照合用test.setファイルをCSV化
        is_end = _edit_test_file()
        if 0 < len(is_end):
            return is_end

        # CSVファイルからHTML化
        is_end = _output_html()
        if 0 < len(is_end):
            return is_end

        return []


# .setファイルをCSV化
def _edit_setfiles():

    read_files = []
    err_msg = ''
    paths = os.listdir(PRM_PATHS)
    for path in paths:

        # フォルダでなければパス
        if not os.path.isdir(PRM_PATHS + '/' + path):
            continue

        files = os.listdir(PRM_PATHS + '/' + path)
        read_file = []
        for file in files:
            try:
                # .setファイルでなければパス
                if file.find('.set') < 0:
                    continue

                read_file.append(open(PRM_PATHS + '/' + path + '/' + file, 'r').read())

            except Exception as e:
                err_msg += '\n　' + path + '/' + file
                com.log(str(e))

        read_files.append(read_file)

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    eas = []
    cols = []
    ea_names = []

    # 読み込んだ対象ファイルの整形
    for files in read_files:

        is_col = False
        prms = []

        for file in files:

            datas = file.split('\n')
            col = []
            prm = []
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
        path = cst.PRM_OUT_PATH[cst.PC] + '/Set_' + ea_names[i] + '.csv'

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
            if file.find('.mq4') < 0 or 0 <= file.find(' '):
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
            err_msg += '\n　' + file
            com.log(str(e))

    # エラーファイルが1つでもあれば中断
    if 0 < len(err_msg):
        return ['以下のファイルでエラーが発生しました。' + err_msg, '読み込みエラー', 'E']

    # 整形データの書き出し
    for i in range(0, len(eas)):
        path = cst.PRM_OUT_PATH[cst.PC] + '/Mql_' + ea_names[i] + '.csv'

        with open(path, 'w') as f:

            for n in range(0, len(eas[i])):
                prm = eas[i][n].split(',')

                if 0 == n:
                    f.write('Comments,' + ",".join([(
                        prm[k].split('[')[0].replace('_', '') + "_0" +
                        str(int(prm[k].split('=')[0][prm[k].split('=')[0].find('[') + 1:
                                                     prm[k].split('=')[0].find(']')]) + 1)
                        if 0 <= prm[k].split('=')[0].find('[') else
                        prm[k].split('=')[0].replace('_', '')).replace('s_', '_').capitalize()
                        for k in range(1, len(prm) - 1)]))

                f.write('\n' + prm[0].replace('USD', '') + ',')
                f.write(",".join([prm[k].split('=')[1] for k in range(1, len(prm) - 1)]))

            com.log('ファイル作成: ' + path)
    return []


# 照合用test.setファイルをCSV化
def _edit_test_file():

    file = PRM_PATHS + '/test.set'
    try:
        with open(file, 'r') as infile:
            datas = infile.read().split('\n')

            with open(cst.PRM_OUT_PATH[cst.PC] + '/TestSet.csv', 'w') as outfile:

                col = ''
                prm = ''

                for data in datas:

                    if 0 <= data.find(',') or 0 <= data.find('_____'):
                        continue
                    vals = data.split('=')
                    col += vals[0] + ','

                    try:
                        val = vals[1]
                        if 'Comments' == vals[0]:
                            val = val.split('_')[1]
                    except:
                        val = ''

                    prm += val + ','

                outfile.write(col[:-2] + '\n')
                outfile.write(prm[:-2])

        com.log('ファイル作成: ' + cst.PRM_OUT_PATH[cst.PC] + '/TestSet.csv')

    except Exception as e:
        com.log(str(e))
        return ['以下のファイルでエラーが発生しました。' + file, '読み込みエラー', 'E']

    return []


# CSVファイルからHTML化
def _output_html():

    read_sets = []
    read_mqls = []

    # 作成したCSVを全て、種類分けしながら読み込む
    files = os.listdir(cst.PRM_OUT_PATH[cst.PC])
    for file in files:
        try:
            if 0 <= file.find('Set_'):
                read_sets.append([file, pd.read_csv(cst.PRM_OUT_PATH[cst.PC] + '/' + file)])
            elif 0 <= file.find('Mql_'):
                read_mqls.append([file, pd.read_csv(cst.PRM_OUT_PATH[cst.PC] + '/' + file)])
            elif 0 <= file.find('Test'):
                read_set = pd.read_csv(cst.PRM_OUT_PATH[cst.PC] + '/' + file)

        except Exception as e:
            com.log(str(e))
            return ['以下のファイルでエラーが発生しました。' + file, '読み込みエラー', 'E']

    for ea in read_sets:
        ea_name = ea[0].split('_')[1].replace('.csv', '')

        # HTMLヘッダー
        html = '<html><head><title>' + ea_name + '</title>'
        html += '</head><body><div align="center">'
        html += '<table><tr><td class="eaName" align="center">' + ea_name + '</td></tr><tr><td>'
        html += '<table cellspacing="0" cellpadding="0"><tr><td>'

        prms = pd.DataFrame.transpose(ea[1])

        for key in prms.index:

            if 0 <= key.find('Logic') or key in ['Positions', 'Safety']:
                continue

            html += '<tr><td class="col" align="left">' + key + '</td>'

            for i in range(0, len(prms)):
                try:
                    html += '<td class="prm" align="' + ('center' if 'Comments' == key else 'right') + \
                            '">' + str(prms[i][key]) + '</td>'
                except: pass

            html += '</tr>'

        # HTMLフッター
        html += '</table></td></tr></table></div><style type="text/css">'
        html += '.eaName{padding: 10px; background: #FFCCFF;}'
        html += '.col{border: 1px solid #DDDDDD; padding: 5px 15px; background: #CCFFFF;}'
        html += '.prm{border: 1px solid #DDDDDD; padding: 5px;}'

        html += '</style></body></html>'

        path = cst.PRM_OUT_PATH[cst.PC] + '/' + ea_name + '.html'
        with open(path, 'w') as f:
            f.write(html)
        com.log('ファイル作成: ' + path)

    return []
