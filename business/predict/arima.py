#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import numpy as np
import statistics
import pandas as pd
import FreeSimpleGUI as sg


from sklearn.metrics import r2_score
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout

import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


def create(dict_df, inputs):

    fig, ax = plt.subplots(1, len(dict_df), figsize=cst.FIG_SIZE)
    fig.suptitle('ARIMA: ',
                 fontsize=14, fontname='Yu Gothic')

    total_time = 0
    cnt = 0
    try:
        for currency in dict_df:
            start_time = com.time_start()

            window = com.progress('ARIMAモデル作成中', [currency, len(dict_df)], interrupt=True)
            event, values = window.read(timeout=0)

            window[currency].update(currency + ' (' + str(cnt) + ' / ' + str(len(dict_df)) + ')')
            window[currency + '_'].update(cnt)

            df = dict_df[currency]
            # Close(終値)のデータ
            data = df.filter(['Close'])
            dataset = data.values



            run_time = com.time_end(start_time)
            total_time += run_time
            com.log('ARIMA[' + currency + ']予測完了(' + com.conv_time_str(run_time) + ') ')

            cnt += 1
            window.close()

        plt.gcf().autofmt_xdate()
        plt.legend(['Train', 'Val', 'Predictions'], loc='lower center')
        plt.show()
    finally:
        try: window.close()
        except: pass

    com.log('LSTMモデル作成完了(' + com.conv_time_str(total_time) + ')')

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
