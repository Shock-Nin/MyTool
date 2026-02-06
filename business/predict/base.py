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
import joblib

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import warnings
warnings.simplefilter(action='ignore')

YEAR_MINUS = 1

now = datetime.datetime.now().year - YEAR_MINUS
END_YEAR = ['終了年　　　　', [str(year) for year in range(now - 15, now + 1)], str(now - 1)]
TERM_YEAR = ['期間　　　　　', [str(term) for term in range(1, 15)], '5']

MAIN_MODELS = ['LSTM', 'GRU', 'RNN', 'ARIMA']

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

    def _optimize(self):
        inputs = com.input_box('選択してください。', '分析選択', [
            ['時間足　　　　', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
            ['通貨　　　　　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
            END_YEAR,
            TERM_YEAR,
            ['モデル　　　　', ['簡易チャート', 'AUTO_ARIMA', 'AutoReg'], '簡易チャート'],
            # ['モデル', ['移動平均', 'LSTM', 'GRU', 'RNN', 'ARIMA'], '移動平均'],
        ], obj='combo')
        if inputs[0] <= 0:
            return

        self.period = inputs[1][0]
        self.currency = inputs[1][1]
        self.years = [str(int(inputs[1][2]) - int(inputs[1][3]) + 1), str(int(inputs[1][2]) + 1)]
        self.model = inputs[1][4]

        self._get_data()

        match self.model:
            case '簡易チャート':
                inputs = com.input_box('期間を設定してください。', '期間選択', [
                    ['MA　　　　　　　', '7,21,50,150,300'],
                    ['季節周期　　　　　', '130' if 'D1' ==self.period else '120']
                ], obj='input')

                if inputs[0] <= 0:
                    return
                self._open_chart(inputs[1][0].split(','), int(inputs[1][1]))

            case 'AUTO_ARIMA':
                inputs = com.input_box('最適化範囲を設定してください。', '最適化範囲選択', [
                    ['PDQ　　　　　　', '0,1,2']
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.optimize_Arima(self.currency, self.df, inputs[1][0].split(','))
            case 'AutoReg':
                inputs = com.input_box('最適化範囲を設定してください。', '最適化範囲選択', [
                    ['ARラグ　　　　　　　　　　　', ','.join([str(lag) for lag in range(5, 205, 5)])],
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.optimize_Ar(self.currency, self.df, inputs[1][0].split(','))

    def _analytics(self):
        inputs = com.input_box('選択してください。', '分析選択', [
            ['時間足　　　　', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
            ['通貨　　　　　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
            END_YEAR,
            TERM_YEAR,
            ['モデル　　　　', MAIN_MODELS, 'LSTM'],
            # ['モデル', ['移動平均', 'LSTM', 'GRU', 'RNN', 'ARIMA'], '移動平均'],
        ], obj='combo')
        if inputs[0] <= 0:
            return

        self.period = inputs[1][0]
        self.currency = inputs[1][1]
        self.years = [str(int(inputs[1][2]) - int(inputs[1][3]) + 1), str(int(inputs[1][2]) + 1)]
        self.model = inputs[1][4]

        self._get_data()

        match self.model:
            case 'LSTM' | 'GRU'| 'RNN':
                inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
                    ['予測期間　　　', str(self._get_forecast_start())],
                    ['予測間隔　　　', '120'],
                    ['予測数　　　　', '90'],
                    ['中間層　　　　', '200'],
                    ['ドロップ　　　', '0.2'],
                    ['エポック　　　', '30'],
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import keras_models
                keras_models.run(self.model, self.currency, self.df, int(inputs[1][0]), int(inputs[1][1]),
                                 int(inputs[1][2]), int(inputs[1][3]), float(inputs[1][4]), int(inputs[1][5]))

            case 'ARIMA':
                inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
                    ['予測期間　　　　　', str(self._get_forecast_start())],
                    ['予測間隔　　　　　', '5'],
                    # ['シミュレーション　', '1000'],
                    # ['バンド幅　　　　　', '25'],
                    ['PDQ　　　　　　', '2,1,2'],
                    ['ARラグ　　　　　', '100']
                ], obj='input')

                if inputs[0] <= 0:
                    return

                from business.predict import arima
                arima.run(self.currency, self.df,
                          int(inputs[1][0]),
                          int(inputs[1][1]),
                          inputs[1][2],
                          int(inputs[1][3]),
                          # ('-' if 'AutoReg' == self.model else int(inputs[1][2])),
                          # ('-' if 'AutoReg' == self.model else inputs[1][3]),
                          # int(inputs[1][1 if 'AutoReg' == self.model else 4]),
                          )

    def _load_model(self):

        path = f'{cst.MODEL_PATH[cst.PC]}models'
        files = []
        is_exist = False
        for fold in MAIN_MODELS:
            target = [f for f in os.listdir(f'{path}/{fold}/Model') if f.find('.DS') < 0]
            files.append([fold, list(sorted(target, reverse=True))])
            if 0 < len(target):
                is_exist = True

        if not is_exist:
            com.dialog('モデルファイルが存在しません。', 'モデルファイル不在')
            return

        layout = []
        for fold in files:
            if 0 < len(fold[1]):
                for file in fold[1]:
                    layout.append(fold[0] + ''.join('  ' for _ in range(6 - len(fold[0]))) + '/' + file)
        # layout = [[fold[0] + '/' + file for file in fold[1]] for fold in files if 0 < len(fold[1])]

        inputs = com.input_box('選択してください。', 'データ選択', [
            ['', layout, layout[0]],
            ['時間足　　　　', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
            ['通貨　　　　　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
            ['開始年　　　　', [i for i in range(now - 9, now + 1)], str(now)],
            ['開始月　　　　', [i for i in range(1, 13)], str(datetime.datetime.now().month)],
            ['開始日　　　　', [i for i in range(1, 32)], str(datetime.datetime.now().day)],
            ['予測期間　　　', [7, 14, 21, 30, 90, 180, 365], '180'],
            ['表示年数　　　', [i for i in range(1, 20)], '5']
        ], obj='combo')
        if inputs[0] <= 0:
            return


        path += f'/{inputs[1][0].split('/')[0].replace(' ', '')}/Model/{inputs[1][0].split('/')[1]}'

        self.period = inputs[1][1]
        self.currency = inputs[1][2]
        forecast = inputs[1][6]

        train_end = [inputs[1][3], inputs[1][4], inputs[1][5]]
        train_start = [int(inputs[1][3]) - int(inputs[1][7]), inputs[1][4], inputs[1][5]]
        test_days = _get_test_days(train_end, forecast)
        print(train_start, train_end)
        self._get_data(train_start, test_days)

        df_date = self.df.index[-1].split('-')
        df_date = datetime.datetime(int(df_date[0]), int(df_date[1]), int(df_date[2]))
        # add_df = _add_forecast_data(self.period, df_date, test_days, self.df.at[self.df.index[-1], 'Close'])
        #
        # if add_df is not None:
        #     self.df = pd.concat([self.df, add_df])

        msg = f'予測内容を設定してください\n\n{str(self.df.index[0])} - {str(df_date)[:10]}'
              # + f'{'' if add_df is None else ' | ' + add_df.index[-1]}\n'

        if path.endswith('.keras'):

            from tensorflow.keras.models import load_model
            loaded_result = load_model(path)

            # モデルのパラメータを取得
            middle = None
            dropout = -1
            model_type = None

            for layer in loaded_result.layers:
                layer_config = layer.get_config()
                layer_name = layer.__class__.__name__

                # モデルタイプを取得（LSTM, GRU, SimpleRNN）
                if layer_name in ['LSTM', 'GRU', 'SimpleRNN']:
                    model_type = layer_name if layer_name != 'SimpleRNN' else 'RNN'
                    middle = layer_config.get('units')

                # Dropout率を取得
                if 'Dropout' == layer_name:
                    dropout = layer_config.get('rate', -1)

            inputs = com.input_box(f'{msg}モデル: {model_type}, middle={middle}, dropout={dropout}', 'モデル実行', [
                ['予測間隔　　　', '120'],
                ['予測数　　　　', '90'],
                ['中間層　　　　', str(middle) if middle else '200'],
                ['ドロップ　　　', str(dropout) if 0 <= dropout else '0.2'],
                ['エポック　　　', '30'],
            ], obj='input')

            if inputs[0] <= 0:
                return

            from business.predict import keras_models
            keras_models.run(model_type, self.currency, self.df, forecast, int(inputs[1][0]),
                             int(inputs[1][1]), int(inputs[1][2]), float(inputs[1][3]), int(inputs[1][4]), loaded_result)

        elif path.endswith('.pkl'):

            # モデルの読み込み
            loaded_result = joblib.load(path)
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
                    str_model = row.split('(')[-1].split(')')[0].split()[-1]



            print(start_len, sample)

            # if 'SARIMAX' == model_type:
            # if 'ARIMA' == model_type:
            inputs = com.input_box(msg, 'モデル実行', [
                ['予測間隔　　　', '5']], obj='input')
                # ['シミュレーション　', '1000'], ['バンド幅　　　　　', '25']], obj='input')
            if inputs[0] <= 0:
                return

            from business.predict import arima
            # if 'SARIMAX' == model_type:
            if 'ARIMA' == model_type:
                arima.run(self.currency, self.df, forecast, int(inputs[1][0]),# int(inputs[1][1]),
                          str_pdq.replace(' ', '')[1: -1], '', loaded_result=loaded_result)
            else:
                arima.run(self.currency, self.df, forecast, int(inputs[1][0]),
                          '-', str_model, loaded_result=loaded_result)

            # if 2 == sample[0].count('-'):
            #     self.years = [sample[0][-4:], str(int(sample[1][-4:]) + 2)]
            #
            # # self._get_data()
            #
            # if 2 != sample[0].count('-'):
            #     self.years = [self.df.index[len(self.df) - start_len][:4], str(int(self.df.index[-1][:4]) + 1)]


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

    def _get_data(self, train_start=None, test_days=None):

        df = pd.read_csv(cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', '') + self.period + '.csv')
        for col in df.columns:
            if col not in ['Time', self.currency]: del df[col]

        df.columns = ['Time', 'Close']
        if train_start is not None:
            df['Time'] = df['Time'].astype('datetime64[us]')
            df = df[(datetime.datetime(train_start[0], train_start[1], train_start[2]) <=
                     df['Time']) & (df['Time'] < test_days[-1])]
        if self.years is not None:
            df = df[(self.years[0] <= df['Time']) & (df['Time'] < self.years[1])]
        df['Time'] = df['Time'].astype(str)
        df = df.set_index('Time')

        self.df = df
        print('取得完了: ' + self.period + ': ' + str(self.currency) + ' '
              + str(df.index[0])[:10] + '～' + str(df.index[-1])[:10])

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
        forecast = len(self.df) - 1
        cnt = forecast
        # 終了年の一年前を取得
        while int(self.df.index[cnt][:4]) == int(self.df.index[-1][:4]):
            forecast = cnt
            cnt -= 1
        return len(self.df) - forecast

# # 現在年の前年・現在年の営業日で、空値データを設定
# def _add_forecast_data(period, start, test_days, price=None):
#     ymd = start + datetime.timedelta(days=1)
#
#     list_dt = []
#     list_price = []
#     while ymd < test_days[-1]:
#         if ymd.weekday() not in [5, 6] and not (ymd.month == 1 and ymd.day == 1):
#             if 'D1' == period:
#                 list_dt.append(ymd)
#                 list_price.append(price)
#             else:
#                 for h in range(0, 24):
#                     list_dt.append(datetime.datetime(ymd.year, ymd.month, ymd.day, ymd.hour, 0, 0))
#                     list_price.append(price)
#
#         ymd += datetime.timedelta(days=1)
#
#     if 0 == len(list_dt):
#         return None
#
#     df = pd.DataFrame(index=range(len(list_dt)), columns=['Time', 'Close'])
#     df['Time'] = pd.DataFrame(list_dt).astype(str)
#     if price is not None:
#         df['Close'] = pd.DataFrame(list_price).astype(float)
#     df = df.set_index('Time')
#
#     return df

def _get_test_days(input_date, forecast):
    test_days = []
    dt = datetime.datetime(int(input_date[0]), int(input_date[1]), int(input_date[2]))

    for i in range(forecast):
        if dt.weekday() not in [5, 6] and not (dt.month == 1 and dt.day == 1):
            test_days.append(datetime.datetime(dt.year, dt.month, dt.day))
        dt += datetime.timedelta(days=1)
    return test_days

    # def _create_model(self):
    #     inputs = com.input_box('選択してください。', 'モデル作成', [
    #         ['時間足　　', cst.MODEL_PERIODS, cst.MODEL_PERIODS[0]],
    #         ['通貨　　　', cst.MODEL_CURRENCIES, cst.MODEL_CURRENCIES[0]],
    #         START_YEAR,
    #         END_YEAR,
    #         ['モデル　　', MAIN_MODELS, 'ARIMA'],
    #     ], obj='combo')
    #     if inputs[0] <= 0:
    #         return
    #
    #     self.period = inputs[1][0]
    #     self.currency = inputs[1][1]
    #     self.years = [inputs[1][2], inputs[1][3]]
    #     self.model = inputs[1][4]
    #
    #     self._get_data()
    #
    #     match self.model:
    #         case 'LSTM' | 'GRU'| 'RNN':
    #             inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
    #                 ['予測間隔　　　', '120'],
    #                 ['中間層　　　　', '200'],
    #                 ['ドロップ　　　', '0.2'],
    #                 ['エポック　　　', '30'],
    #             ], obj='input')
    #
    #             if inputs[0] <= 0:
    #                 return
    #
    #             from business.predict import keras_models
    #             keras_models.save(self.model, self.currency, self.df, int(inputs[1][0]), int(inputs[1][1]),
    #                               float(inputs[1][2]), int(inputs[1][3]))
    #
    #         case 'ARIMA':
    #             inputs = com.input_box('パラメータを設定してください。', 'パラメータ選択', [
    #                 ['PDQ　　　　　　', '2,1,2'],
    #                 ['PDQS　　　　　', '2,1,2,' + ('130' if 'D1' ==self.period else '120')],
    #                 ['ARラグ　　　　　', '100'],
    #             ], obj='input')
    #
    #             if inputs[0] <= 0:
    #                 return
    #
    #             from business.predict import arima
    #             arima.save(self.currency, self.df, inputs[1][0], inputs[1][1], int(inputs[1][2]))
