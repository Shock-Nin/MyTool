#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from common import com
from const import cst

import pandas as pd
import FreeSimpleGUI as sg
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


class Base:

    def __init__(self, function):
        self.function = function
        self.dict_df = None
        self.years = None
        self.period = None
        self.input = None

    def do(self):
        getattr(self, '_' + self.function)()

    def _get_csv(self, msg):
        inputs = com.input_box(msg, '開始確認', [
            ['開始年　　　　', int(com.str_time()[:4]) - 7],
            ['終了年　　　　', int(com.str_time()[:4]) - 5],
            ['時間足　　　　', 'D1'],
            ['通貨　　　　　', 'EUR,GBP,JPY'],
            ['MA　　　　　', '10,30,50'] if 'open_chart' == self.function else ['予測期間とエポック', '50,25']],
                               obj='input')
        if inputs[0] <= 0:
            return

        currencies = []
        for currency in inputs[1][3].split(','):
            if 'JPY' == currency:
                currency = 'USD' + currency
            else:
                currency += 'USD'
            currencies.append(currency)

        self.years = [datetime.datetime(int(inputs[1][0]), 1, 1, 0, 0, 0),
                 datetime.datetime(int(inputs[1][1]) + 1, 1, 1, 0, 0, 0)]
        self.period = inputs[1][2]
        self.input = inputs[1][4].split(',')

        dict_df = {}

        for currency in currencies:
            df = pd.read_csv(cst.HST_PATH[cst.PC].replace('\\', '/') + ('_d1/' if 'D1' == self.period else '_h1/') + currency + '.csv', header=None)
            df.columns = (['Time'] if 'D1' == self.period else ['Time', 'Hour']) + ['Open', 'High', 'Low', 'Close']

            df['Time'] = df['Time'].astype(str)
            if 'D1' == self.period:
                df['Time'] = pd.to_datetime(df['Time'], format='%Y%m%d')
            else:
                df['Hour'] = df['Hour'].astype(str)
                df['Time'] = df['Time'].str.cat(df['Hour'], sep=' ')
                df['Time'] = pd.to_datetime(df['Time'], format='%Y%m%d %H')
                del df['Hour']

            df = df[(self.years[0] <= df['Time']) & (df['Time'] < self.years[1])]

            df = df.set_index('Time')
            dict_df[currency] = df

        self.dict_df = dict_df
        print('取得完了: ' + self.period + str(currencies).replace('\'', '') + ' '
              + str(self.years[0])[:10] + '～' + str(self.years[1])[:10])

    def _open_chart(self):
        self._get_csv('チャート表示')
        if self.dict_df is None or self.input is None:
            return

        fig, ax = plt.subplots(1, len(self.dict_df), figsize=cst.FIG_SIZE)
        fig.suptitle(', '.join(currency.replace('USD', '') for currency in self.dict_df))

        cnt = 0
        for currency in self.dict_df:
            df = self.dict_df[currency]

            ax[cnt].plot(df.index, df['Close'], linewidth=2)

            for ma in self.input:
                col_name = f'MA {ma}'
                df[col_name] = df['Close'].rolling(int(ma)).mean()
                ax[cnt].plot(df[col_name], linewidth=1, linestyle='dashed')
            cnt += 1

        plt.gcf().autofmt_xdate()
        plt.legend(['Close'] + ['MA ' + str(ma) for ma in self.input], loc='lower center')
        plt.show()

    def _create_model(self):

        self._get_csv('モデル作成')
        if self.dict_df is None:
            return

        inputs = com.input_box('モデルを選択してください。', 'モデル選択',
                               [['LSTM,GRU,RNN,ARIMA', 'LSTM']], obj='combo')
        if inputs[0] <= 0:
            return

        if 'ARIMA' == inputs[1][0]:
            from business.predict import arima
            arima.create(self.dict_df, self.input)

        # elif 'RNN' == inputs[1][0]:
        #     from business.predict import rnn
        #     rnn.create(inputs[1][0], self.dict_df, self.input)
        else:
            # from business.predict import rnn
            # rnn.create(inputs[1][0], self.dict_df, self.input)
            from business.predict import keras_models
            keras_models.create(inputs[1][0], self.dict_df, self.input)

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
