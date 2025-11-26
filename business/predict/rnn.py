#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import numpy as np
import statistics
import pandas as pd
import FreeSimpleGUI as sg

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import Activation
from tensorflow.keras.layers import SimpleRNN
from tensorflow.keras.layers import GRU

import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

# データとしては約四年分あるが、今回はこれを8このパートに分けて、それぞれの領域で予想を行う
TERM_PART_LIST = [0, 120, 240, 360, 480, 600, 720, 840]

# 予測に利用するデータ数
# 90個のデータから後の30個のデータを予測する
NUM_LSTM = 90

# 中間層の数
NUM_MIDDLE = 200


def create(dict_df, inputs):
    com.log('RNNモデル作成開始')

    fig, ax = plt.subplots(1, len(dict_df), figsize=(16, 6))
    fig.suptitle('RNN [' + ', '.join(currency.replace('USD', '') for currency in dict_df) + ']')


    total_time = 0
    cnt = 0
    try:
        for currency in dict_df:
            start_time = com.time_start()

            window = com.progress('RNNモデル作成中', [currency, len(dict_df)], interrupt=True)
            event, values = window.read(timeout=0)

            window[currency].update(currency + ' (' + str(cnt) + ' / ' + str(len(dict_df)) + ')')
            window[currency + '_'].update(cnt)

            df = dict_df[currency]


            for term in [1, 2, 3, 4, 5, 6]:
                n, date, x, y, l_x, l_y = _get_x_y_lx_ly(df, term)
                model = _build_model('RNN')
                # model = build_model('LSTM')
                # model = build_model('GRU')
                history = model.fit(l_x, l_y, epochs=int(inputs[1]), batch_size=32, validation_split=0.25,
                                    verbose=0)
                print('予測期間 : {} - {} の結果'.format(date[0], date[NUM_LSTM - 1]))
                _plot_result(model, n, date, x, y, l_x, l_y)


            loss = history.history['loss']
            val_loss = history.history['val_loss']

            ax[cnt].plot(np.arange(len(loss)), loss, label='loss')
            ax[cnt].plot(np.arange(len(val_loss)), val_loss, label='val_loss')

            cnt += 1
            window.close()

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log(currency + '予測完了(' + com.conv_time_str(run_time) + ') ')

        plt.gcf().autofmt_xdate()
        plt.grid()
        # plt.legend(['Train', 'Val', 'Predictions'], loc='lower center')
        plt.legend()
        plt.show()
    finally:
        try: window.close()
        except: pass

    com.log('RNNモデル作成完了(' + com.conv_time_str(total_time) + ')')

def _get_x_y_lx_ly(df, term_part):
    print(df)
    date = np.array(df.index[TERM_PART_LIST[term_part]: TERM_PART_LIST[term_part + 1]])
    x = np.array(df.index.values[TERM_PART_LIST[term_part]: TERM_PART_LIST[term_part + 1]])
    y = np.array(df['Close'][TERM_PART_LIST[term_part]: TERM_PART_LIST[term_part + 1]])

    n = len(y) - NUM_LSTM
    l_x = np.zeros((n, NUM_LSTM))
    l_y = np.zeros((n, NUM_LSTM))

    for i in range(0, n):
        l_x[i] = y[i: i + NUM_LSTM]
        l_y[i] = y[i + 1: i + NUM_LSTM + 1]

    l_x = l_x.reshape(n, NUM_LSTM, 1)
    l_y = l_y.reshape(n, NUM_LSTM, 1)

    return n, date, x, y, l_x, l_y


def _build_model(model_name='RNN'):
    # LSTMニューラルネットの構築
    model = Sequential()

    # RNN,LSTM、GRUを選択できるようにする
    if model_name == 'RNN':
        model.add(SimpleRNN(NUM_MIDDLE, input_shape=(NUM_LSTM, 1), return_sequences=True))

    if model_name == 'LSTM':
        model.add(LSTM(NUM_MIDDLE, input_shape=(NUM_LSTM, 1), return_sequences=True))

    if model_name == 'GRU':
        model.add(GRU(NUM_MIDDLE, input_shape=(NUM_LSTM, 1), return_sequences=True))

    model.add(Dense(1, activation="linear"))
    model.compile(loss="mean_squared_error", optimizer="sgd")

    return model

def _plot_result(model, n, date, x, y, l_x, l_y):

    # 初期の入力値
    res = []
    res = np.append(res, l_x[0][0][0])
    res = np.append(res, l_y[0].reshape(-1))

    for i in range(0, n):
        _y = model.predict(res[- NUM_LSTM:].reshape(1, NUM_LSTM, 1))

        # 予測されたデータを次の予測のためのインプットデータとして利用
        res = np.append(res, _y[0][NUM_LSTM - 1][0])

    res = np.delete(res, -1)

    plt.plot(date, y, label="stock price", color='coral')
    plt.plot(date, res, label="prediction result", color='blue')
    plt.xticks(date[::12], rotation=60)

    plt.legend()
    plt.grid()

    plt.axvspan(0, NUM_LSTM, color="coral", alpha=0.2)

    plt.show()

    print('{} - {} の結果'.format(date[0], date[NUM_LSTM - 1]))

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
