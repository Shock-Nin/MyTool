#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import datetime

from common import com
from const import cst

import numpy as np
import pandas as pd

from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

YEAR_MINUS = 1

now = datetime.datetime.now().year - YEAR_MINUS
START_YEAR = ['開始年', [str(year) for year in range(2004, now - 2)], str(now - 4)]
# START_YEAR = ['開始年', [str(year) for year in range(2004, now - 2)], str(now - 12)]
# START_YEAR = ['終了年', [str(year) for year in range(now - 15, now)], str(now)]
END_YEAR = ['終了年', [str(year) for year in range(now - 15, now)], str(now - 1)]

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

    def _analytics(self):
        inputs = com.input_box('選択してください。', '分析選択', [
            ['時間足', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
            ['通貨　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
            START_YEAR,
            END_YEAR,
            ['モデル', ['季節トレンド', 'LSTM', 'GRU', 'RNN', 'ARIMA', 'AR', 'AUTO_ARIMA', 'AUTO_ARIMA_S'], 'ARIMA'],
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
            case '季節トレンド':
                inputs = com.input_box('期間を設定してください。', '期間選択', [
                    ['MA　　　　　　　', '7,21,50,150,300'],
                    ['季節周期　　　　　', '130' if 'D1' ==self.period else '120']
                ], obj='input')

                if inputs[0] <= 0:
                    return
                self._open_chart(inputs[1][0].split(','), int(inputs[1][1]))

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

            case 'AUTO_ARIMA' | 'AUTO_ARIMA_S':
                inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
                    ['季節周期　　　　　', '130' if 'D1' ==self.period else '120'],
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.optimize_Arima(self.currency, self.df, int(inputs[1][0]), 'AUTO_ARIMA_S' == self.model)
            case 'ARIMA' | 'AR':
                inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
                    ['季節周期　　　　　', '130' if 'D1' ==self.period else '120'],
                    ['予測期間　　　　　', str(self._get_forecast_start())],
                    ['シミュレーション　', '1000'],
                    ['バンド幅　　　　　', '25'],
                    ['PDQ　　　　　　', '2,1,2'],
                    ['PDQS　　　　　', '2,1,2'],
                    ['予測間隔　　　　　', 1],
                    ['ARラグ　　　　　', '100']
                ] if 'ARIMA' == self.model else [
                    ['予測期間　　　　　', str(self._get_forecast_start())],
                    ['予測間隔　　　　　', 1],
                    ['ARラグ　　　　　', '100']
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.run(self.currency, self.df,
                          ('-' if 'AR' == self.model else int(inputs[1][0])),
                          int(inputs[1][0 if 'AR' == self.model else 1]),
                          int(inputs[1][1 if 'AR' == self.model else 6]),
                          ('-' if 'AR' == self.model else int(inputs[1][2])),
                          ('-' if 'AR' == self.model else int(inputs[1][3])),
                          ('-' if 'AR' == self.model else inputs[1][4]),
                          ('-' if 'AR' == self.model else inputs[1][5]),
                          int(inputs[1][2 if 'AR' == self.model else 7]),
                          ar_only='AR' == self.model)

    def _create_model(self):
        inputs = com.input_box('選択してください。', 'モデル作成', [
            ['時間足', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
            ['通貨　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
            START_YEAR,
            END_YEAR,
            ['モデル', ['LSTM', 'GRU', 'RNN', 'ARIMA'], 'ARIMA'],
        ], obj='combo')
        if inputs[0] <= 0:
            return

        self.period = inputs[1][0]
        self.currency = inputs[1][1]
        self.years = [inputs[1][2], inputs[1][3]]
        self.model = inputs[1][4]

        self._get_data()

        match self.model:
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
                    ['季節周期　　　　　', '130' if 'D1' ==self.period else '120'],
                    ['PDQ　　　　　　', '2,1,2'],
                    ['PDQS　　　　　', '2,1,2'],
                    ['ARラグ　　　　　', '100'],
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.save(self.currency, self.df, int(inputs[1][0]), inputs[1][1], inputs[1][2], int(inputs[1][3]))

    def _load_model(self):

        self._get_year_blank('D1')

        path = f'{cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'models')}/Model'
        files = os.listdir(path)

        if 0 == len(files):
            com.dialog('モデルファイルが存在しません。', 'モデルファイル不在')
            return
        files = list(sorted([file for file in files if 0 <= file.find('.pkl')], reverse=True))
        if 0 == len(files):
            com.dialog('モデルファイルが存在しません。', 'モデルファイル不在')
            return

        inputs = com.input_box('選択してください。', 'モデル実行', [
            ['モデル', files, files[0]],
            START_YEAR,
            END_YEAR,
        ], obj='combo')
        if inputs[0] <= 0:
            return
        path += '/' + inputs[1][0]

        if path.endswith('.pkl'):

            # モデルの読み込み
            from statsmodels.tsa.arima.model import ARIMAResults
            loaded_result = ARIMAResults.load(path)

            self.period = list(loaded_result.model.data.row_labels)[0]
            self.period = ('D1' if 10 == len(self.period) else 'H1')

            summary = str(loaded_result.summary()).splitlines()
            print(loaded_result.summary())
            for i in range(len(summary)):
                row = summary[i]
                if row.startswith('Dep. Variable:'):
                    self.currency = row.split()[2]
                    start_len = int(row.split('No. Observations:')[1])
                elif row.startswith('Sample:'):
                    sample = [row.split()[1], summary[i + 1].replace(' ', '')]
                elif row.startswith('Model:'):
                    model_type = row.split()[1].split('(')[0]
                    str_pdq = '(' + row.split('(')[1].split(')')[0] + ')'
                    span = row.split('(')[-1].split(')')[0].split()[-1]
                    str_pdqs = ('' if 0 == row.count('x') else row.split('x')[1].split(')')[0] + ')')

        print(start_len, sample)
        self.years = [str(inputs[1][1]), str(int(inputs[1][2]))]
        self._get_data()

        msg = (f'PDQ{str_pdq}, PDQS{str_pdqs}' if 'SARIMAX' == model_type else f'ARラグ({span})')
        if 'SARIMAX' == model_type:
            input = [['シミュレーション　', '1000'], ['バンド幅　　　　　', '25']]
        else:
            input = [['予測間隔　　　　　', 1]]
        inputs = com.input_box(f'予測内容を設定してください。\n\n{inputs[1][0]}\n{str(self.years[0])} - {str(self.years[1])} , {msg}',
                               'モデル実行', [
            ['予測期間　　　　　', str(self._get_forecast_start())],

        ] + input, obj='input')
        if inputs[0] <= 0:
            return

        str_pdqs = str(str_pdqs.split(' ')[:3]).replace('\'', '').replace('[', '').replace(']', '').replace(' ', '')[1:]
        from business.predict import arima
        if 'SARIMAX' == model_type:
            arima.run(self.currency, self.df, int(span), int(inputs[1][0]), '-', int(inputs[1][1]),
                      int(inputs[1][2]), str_pdq.replace(' ', '')[1: -1], str_pdqs, int(span), loaded_result=loaded_result)
        else:
            arima.run(self.currency, self.df, '-', int(inputs[1][0]), int(inputs[1][1]), '-',
                      '-', '-', '-', int(span), loaded_result=loaded_result)

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

    def _open_chart(self, mas, span):

        # 季節性分析用のデータ作成
        df_seasonal = self.df.copy().rename(columns={'Close': self.currency})

        # 季節性・残差・対数差分の取得
        advanced_decomposition = STL(df_seasonal[self.currency], period=span, robust=True).fit()
        eq_diff = np.diff(df_seasonal[self.currency], n=1)
        ad_fuller_result = adfuller(eq_diff)

        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=cst.FIG_SIZE,
                                        gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        fig.suptitle(f'{self.currency}[{str(len(self.df))}] 季節周期: {str(span)}, ADF: {str(round(ad_fuller_result[0], 7))}, P-val: {str(round(ad_fuller_result[1], 7))}', fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(self.df.index, self.df['Close'], linewidth=2, alpha=0.5)
        for ma in mas:
            col_name = f'MA {ma}'
            self.df[col_name] = self.df['Close'].rolling(int(ma)).mean()
            ax1.plot(self.df[col_name], linewidth=1, linestyle='dashed', label=col_name, alpha=0.7)
        ax1.plot(advanced_decomposition.trend, label='Trend', linewidth=1, color='pink', alpha=0.7)

        ax2.plot(advanced_decomposition.seasonal, label='季節性(' + str(span) + ')', linewidth=1, alpha=0.5)
        ax2.plot(advanced_decomposition.resid, label='残差', linewidth=1, alpha=0.2)
        ax2.plot(eq_diff, '.', label='対数差分', linewidth=1, alpha=0.2)

        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(self.df), step=(len(self.df) / 10) + 1))

        ax1.legend(ncol=(len(mas) + 1), loc='upper left')
        ax2.legend(ncol=3, loc='upper left')
        plt.grid()
        plt.grid()
        plt.show()

    # 予測を開始するデータのインデックスを取得
    def _get_forecast_start(self):
        forecast = 0
        # インデックスの日付から、終了年の一年前を取得
        for i in range(len(self.df)):
            if int(self.years[1][:4]) - 1 <= int(self.df.index[i][:4]):
                forecast = i
                break
        return len(self.df) - forecast

    # 現在年の前年・現在年の営業日で、空値データを設定
    def _get_year_blank(self, period):
        years = datetime.datetime.now().year
        years = [years - 1, years, years + 1]

        list_year = []
        for i in range(len(years) - 1):
            dt = datetime.datetime(years[i], 1, 1)
            end = datetime.datetime(years[i + 1], 1, 1)
            list_dt = []

            while dt < end:
                if dt.weekday() not in [5, 6] and not (dt.month == 1 and dt.day == 1):
                    if 'D1' == period:
                        list_dt.append(dt)
                    else:
                        for h in range(0, 24):
                            list_dt.append(datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0))

                dt += datetime.timedelta(days=1)

            df = pd.DataFrame(index=range(len(list_dt)), columns=['Time', 'Close'])
            df['Time'] = pd.DataFrame(list_dt).astype(str)
            df = df.set_index('Time')

            list_year.append(df)
        return list_year