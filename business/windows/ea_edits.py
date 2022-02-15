#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

from business. windows import ea_edit_param
from business. windows import ea_edit_unit
from business. windows import ea_edit_stat

import os
import pandas as pd

class EaEdits:

    def __init__(self, job):
        self.myjob = job

    def do(self):

        if com.question('開始しますか？', '開始確認') <= 0:
            return None

        # EAパラメータ
        is_end = ea_edit_param.EaEditParam().do()
        if 0 != is_end:
            return

        # EA成績(個別)
        is_end = ea_edit_unit.EaEditUnit().do()
        if 0 != is_end:
            return

        # EA成績(統合)
        is_end = ea_edit_stat.EaEditStat().do()
        if 0 != is_end:
            return

        com.close(self.myjob)


# リアルパスを規則順ソートで格納
def sort_paths(is_out):

    paths = []
    get_paths = os.listdir(cst.TEST_UNIT[cst.PC])

    for key1 in cst.CURRNCYS_EA:
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
        datas = pd.read_html(lists, encoding='utf8', header=0, na_values=0)[1]
        for i in range(0, len(datas)):

            name = datas.at[i, '名前'].split('_')[0]
            if name not in names:
                names.append(name)

    except Exception as e:
        com.log(str(e))
        return None

    return names
