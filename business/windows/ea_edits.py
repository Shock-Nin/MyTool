#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

from business. windows import ea_edit_param
from business. windows import ea_edit_unit
from business. windows import ea_edit_stat

import os
import pandas as pd

PRM_PATH = cst.GDRIVE_PATH[cst.PC] + cst.PRM_PATH


class EaEdits:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        yesno = com.question('開始しますか？\n「いいえ」でパラメータのみ更新します。', '開始確認', cancel=True)
        if 0 == yesno:
            return

        start_time = com.time_start()
        total_time = 0

        # EAパラメータ
        is_end = ea_edit_param.EaEditParam().do()
        if 0 != is_end:
            return
        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('パラメータ: 作成完了(' + com.conv_time_str(run_time) + ')')

        if yesno < 0:
            com.dialog('パラメータのみ、更新しました。(' + com.conv_time_str(total_time) + ')', self.myjob)
            return

        # EA成績(個別)
        is_end = ea_edit_unit.EaEditUnit().do()
        if 0 != is_end:
            return
        run_time = com.time_end(start_time)
        total_time += run_time
        start_time = com.time_start()
        com.log('EA成績(個別)作成完了(' + com.conv_time_str(run_time) + '): ')

        # EA成績(統合)
        is_end = ea_edit_stat.EaEditStat().do()
        if 0 != is_end:
            return
        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('EA成績(統合): 作成完了(' + com.conv_time_str(run_time) + ')')

        com.log(self.myjob + ': 全終了(' + com.conv_time_str(total_time) + ')')
        com.dialog('完了しました。(' + com.conv_time_str(total_time) + ')', self.myjob)


# .setファイル名のリストを取得
def prm_list():

    paths = os.listdir(PRM_PATH)
    set_files = []
    for key1 in cst.EA_PATHS:
        for path in paths:

            # 並び順でなければパス
            if path != cst.EA_PATHS[key1][0]:
                continue
            # フォルダでなければパス
            if not os.path.isdir(PRM_PATH + path):
                continue

            files = os.listdir(PRM_PATH + path)
            set_file = []

            for key2 in cst.CURRNCYS_EA[0]:
                for file in files:
                    # 並び順でなければパス
                    if file.find(key2) < 0:
                        continue
                    # .setファイルでなければパス
                    if 0 <= file.find('.set'):
                        set_file.append(file)

            set_files.append([path, set_file])
    return set_files


# リアルパスを規則順ソートで格納
def sort_paths(is_out):

    paths = []
    get_paths = os.listdir(cst.TEST_UNIT[cst.PC])

    for key1 in cst.CURRNCYS_EA[0]:
        for key2 in cst.EA_PATHS:

            for get_path in get_paths:

                if 1 == len(cst.EA_PATHS[key2]):
                    is_key = (get_path == cst.EA_PATHS[key2][0])
                    path = cst.TEST_UNIT[cst.PC] + cst.EA_PATHS[key2][0]
                else:
                    is_key = (get_path == cst.EA_PATHS[key2][1] + key1)
                    path = cst.TEST_UNIT[cst.PC] + cst.EA_PATHS[key2][1] + key1

                # 並び順でなければパス
                if not is_key:
                    continue

                get_files = os.listdir(path)
                get_files.sort()
                files = []

                for get_file in get_files:
                    if 0 <= get_file.find(key1) and 0 <= get_file.find('.htm'):
                        files.append(path.replace(cst.TEST_UNIT[cst.PC], cst.TEST_OUT_PATH[cst.PC]
                                     if is_out else cst.TEST_UNIT[cst.PC]) + '/' + get_file)

                paths.append(files)
    return paths


def name_list(lists):

    names = []
    try:
        datas = pd.read_html(lists, encoding='utf8', header=0, na_values=0)[0]
        for i in range(0, len(datas)):

            name = datas.at[i, cst.EA_DATA_NAMES[0]].split('_')[0]
            if name not in names:
                names.append(name)

    except Exception as e:
        com.log(str(e))
        return None

    return names
