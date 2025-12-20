#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from common import com
from const import cst

import numpy as np
import pandas as pd
import FreeSimpleGUI as sg

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


class Base:

    def __init__(self, function):
        self.function = function
        self.df = None

        self.period = None
        self.currency = None
        self.years = None
        self.model = None

        self.span = None

    def do(self):
        getattr(self, '_' + self.function)()

    def _main(self):

        now = datetime.datetime.now().year
        inputs = com.input_box('選択してください。', 'モデル選択', [
            ['時間足', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
            ['通貨　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
            ['開始年', [str(year) for year in range(2004, now - 2)], str(now - 4)],
            # ['開始年', [str(year) for year in range(2004, now - 2)], str(now - 12)],
            ['終了年', [str(year) for year in range(now - 15, now)], str(now)],
            ['モデル', ['移動平均', 'LSTM', 'GRU', 'RNN', 'ARIMA'], 'ARIMA'],
            # ['モデル', ['移動平均', 'LSTM', 'GRU', 'RNN', 'ARIMA'], '移動平均'],
        ], obj='combo')
        if inputs[0] <= 0:
            return

        self.period = inputs[1][0]
        self.currency = inputs[1][1]
        self.years = [inputs[1][2], inputs[1][3]]
        self.model = inputs[1][4]

        self._get_data()

        match self.model:
            case '移動平均':
                inputs = com.input_box('期間を設定してください。', '期間選択', [
                    ['MA　　　　　', '7,21,50,150,300']], obj='input')

                if inputs[0] <= 0:
                    return
                self._open_chart(inputs[1][0].split(','))

            case 'LSTM' | 'GRU'| 'RNN':
                inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
                    ['学習量　　　　', '0.8'],
                    ['予測期間　　　', '90'],
                    ['エポック　　　', '5'],
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import keras_models
                keras_models.create(self.currency, self.model,  self.df,
                                    float(inputs[1][0]), int(inputs[1][1]) ,int(inputs[1][2]))
                # from business.predict import rnn
                # rnn.create(inputs[1][0], self.df, self.input)

            case 'ARIMA':
                inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
                    ['学習量　　　　', '0.8'],
                    ['季節周期　　　', '12'],
                    ['未来日　　　　', '300'],
                    ['予測間隔　　　', '3'],
                    ['PDQ　　　　', '2,1,2'],
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.create(self.currency, self.df, float(inputs[1][0]), int(inputs[1][1]),
                             int(inputs[1][2]), int(inputs[1][3]), inputs[1][4])

    def _save_model(self):
        pass

    def _load_model(self):
        from business.predict import arima
        path = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'models/') \
                 + 'EURUSD_2022_2024_0.8_30_9_3_2,1,2.pkl'
        arima.load(path)

    def _create_data(self):

        if com.question('データ作成を開始しますか？', '開始確認') <= 0:
            return

        total_time = 0
        cnt = 0
        try:
            for period in cst.MODEL_PERIODS:
                start_time = com.time_start()

                window = com.progress('データ作成中', [period, len(cst.MODEL_PERIODS)], interrupt=True)
                event, values = window.read(timeout=0)

                window[period].update(period + ' (' + str(cnt) + ' / ' + str(len(cst.MODEL_PERIODS)) + ')')
                window[period + '_'].update(cnt)

                dict_df = {}
                times = []

                for currency in cst.MODEL_CURRENCIES:

                    df = pd.read_csv(cst.HST_PATH[cst.PC].replace('\\', '/') + ('_d1/' if 'D1' == period else '_h1/') + currency + '.csv', header=None)
                    df.columns = (['Time'] if 'D1' == period else ['Time', 'Hour']) + ['1', '2', '3', 'Close']

                    df['Time'] = df['Time'].astype(str)
                    if 'D1' == period:
                        df['Time'] = pd.to_datetime(df['Time'], format='%Y%m%d')
                    else:
                        df['Hour'] = df['Hour'].astype(str)
                        df['Time'] = df['Time'].str.cat(df['Hour'], sep=' ')
                        df['Time'] = pd.to_datetime(df['Time'], format='%Y%m%d %H')
                        del df['Hour']
                    for num in ['1', '2', '3']: del df[num]

                    df['Time'] = df['Time'].astype(str)
                    dict_df[currency] = df
                    times += list(df['Time'])

                cur_close = {'Time': []}
                for currency in cst.MODEL_CURRENCIES: cur_close[currency] = []

                times = sorted(list(set(times)))
                year = 0
                for time in times:

                    dt = datetime.datetime.strptime(time, '%Y-%m-%d' + ('' if 'D1' == period else ' %H:%M:%S'))
                    if 5 <= dt.weekday():
                        print('土日: ' + str(time))
                        continue
                    cur_close['Time'].append(time)

                    if 'H1' == period and year != dt.year:
                        com.log('H1: ' + str(time))
                    for currency in dict_df:
                        close = dict_df[currency][(time == dict_df[currency]['Time'])]['Close']
                        cur_close[currency].append('' if 0 == len(close) else str(list(close)[0]))
                    year = dt.year

                pd.DataFrame(cur_close).to_csv(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', '') + period + '.csv', index=False)
                com.log('作成完了: ' + period)

                run_time = com.time_end(start_time)
                total_time += run_time
                com.log(period + 'データ作成完了(' + com.conv_time_str(run_time) + ') ')

                cnt += 1
                window.close()
        finally:
            try:
                window.close()
            except:
                pass

        com.dialog(', '.join([currency for currency in cst.MODEL_CURRENCIES]) + '\n作成完了しました。', 'データ作成完了' )

    def _get_data(self):

        df = pd.read_csv(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', '') + self.period + '.csv')
        for col in df.columns:
            if col not in ['Time', self.currency]: del df[col]

        df.columns = ['Time', 'Close']

        df = df[(self.years[0] <= df['Time']) & (df['Time'] < self.years[1])]
        df['Time'] = df['Time'].astype(str)
        df = df.set_index('Time')

        self.df = df
        print('取得完了: ' + self.period + ': ' + str(self.currency) + ' '
              + str(self.years[0])[:10] + '～' + str(self.years[1])[:10])

    def _open_chart(self, spans):

        fig, ax = plt.subplots(1, 1, figsize=cst.FIG_SIZE, sharex=True)
        fig.suptitle(self.currency + '[' + str(len(self.df)) + '] ', fontsize=cst.FIG_FONT_SIZE)

        plt.plot(self.df.index, self.df['Close'], linewidth=2)

        for ma in spans:
            col_name = f'MA {ma}'
            self.df[col_name] = self.df['Close'].rolling(int(ma)).mean()
            plt.plot(self.df[col_name], linewidth=1, linestyle='dashed')

        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(self.df), step=(len(self.df) / 10) + 1))
        plt.legend(['MA ' + str(ma) for ma in spans], ncol=(len(spans)), loc='upper left')
        plt.grid()
        plt.grid()
        plt.show()

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
