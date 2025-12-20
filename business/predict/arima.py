#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import math

from common import com
from const import cst

import numpy as np
import statistics
import pandas as pd
import FreeSimpleGUI as sg

from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMAResults

from itertools import product
from sklearn.metrics import mean_squared_error
from math import sqrt

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import warnings
warnings.simplefilter(action='ignore')


def create(currency, df, train, span, forecast, interval, str_pqd):

    com.log('ARIMAモデル作成開始')

    # モデルの保存
    save_model = cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'models/') \
                 + f'{currency}_{df.index[0][:4]}_{df.index[-1][:4]}_' \
                 + f'{str(train)}_{str(span)}_{str(forecast)}_{str(interval)}_{str_pqd}.pkl'

    total_time = 0
    cnt = 0
    try:
        start_time = com.time_start()

        window = com.progress('ARIMAモデル作成中', [currency, 2], interrupt=True)
        event, values = window.read(timeout=0)

        window[currency].update(currency + ' 季節性(' + str(cnt) + ' / 3)')
        window[currency + '_'].update(cnt)

        # 基本データからデータ作成
        df_future = df[(datetime.datetime(int(df.index[-1][:4]), 1,1, 0, 0, 0)
                        <= pd.to_datetime(df.index))].copy()
        df_seasonal = df.copy()
        df = df[(pd.to_datetime(df.index)
                 < datetime.datetime(int(df.index[-1][:4]), 1,1, 0, 0, 0))]

        df_future = df_future.rename(columns={'Close': currency})
        df_seasonal = df_seasonal.rename(columns={'Close': currency})
        eq = df.rename(columns={'Close': currency})

        # 季節性・残差・対数差分の取得
        advanced_decomposition = STL(df_seasonal[currency], period=span, robust=True).fit()
        eq_diff = np.diff(df_seasonal[currency], n=1)
        ad_fuller_result = adfuller(eq_diff)

        # 学習データ作成
        split_len = int(np.ceil(len(eq) * train))
        train_data = eq[currency][:split_len]

        # ARIMAのモデル生成、失敗したら終了
        result_df, model = _optimize_Arima(train_data, str_pqd)
        if result_df is None:
            com.dialog('ARIMAのPDQ設定が失敗しました。', 'ARIMA設定失敗')
            return

        cnt += 1
        window[currency].update(currency + ' 予測中(' + str(cnt) + ' / 3)')
        window[currency + '_'].update(cnt)

        # モデルの保存
        model.save(save_model)

        # AICとpdqの抽出
        result_df.sort_values(by='AIC')
        pdq = list(result_df['(p,d,q)'])[0]

        # テストデータを取得
        test_data = eq[currency][split_len:]
        pred_arima = rolling_forecast(eq, len(train_data), len(test_data), interval, pdq)

        # 検証データ作成
        pred_data = pd.DataFrame({'test': test_data})
        pred_data.loc[:, 'predict'] = pred_arima[:len(pred_data)]

        # RMSE取得
        rmse_arima = sqrt(mean_squared_error(pred_data['test'], pred_data['predict']))

        # 予測データ作成
        forcast_data = pd.concat([eq[currency][split_len:], df_future[currency]])
        forecast_arima = rolling_forecast(forcast_data, len(forcast_data), split_len + forecast, interval, pdq)

        # モデルで予測を実行
        # forecast = model.forecast(steps=(len(eq[currency]) - split_len + forecast))
        forecast = model.predict(steps=(len(eq[currency]) - split_len + forecast))
        # print(model.summary())
        # print(model.params)

        cnt += 1
        window[currency].update(currency + ' 予測中(' + str(cnt) + ' / 3)')
        window[currency + '_'].update(cnt)

        std_price = eq[currency][split_len - 1]

        forecast_data = pd.concat([pd.DataFrame({'test': test_data}), pd.DataFrame({'test': df_future[currency]})])
        forecast = [[std_price] + list(forecast.copy()), list(forecast.copy())]

        for i in range(1, len(forecast[0])):
            print(round(forecast[0][i - 1], 5), round(forecast[1][i - 1], 5), round(forecast[1][i - 1] - forecast[0][i - 1], 5))
            # forecast[1][i - 1] -= forecast[0][i - 1]

        forecast = forecast[1]

        for i in range(len(forecast_data)):
            last_price = (std_price if 0 == i else forecast_data.iloc[i - 1]['test'])
            now_price = forecast_data.iloc[i]['test']
            infer = last_price + forecast[i]
            try:
                pred = pred_data.iloc[i]['predict']
            except:
                pred = None

            result_price = (now_price - last_price)
            result_pct = result_price / last_price * 100
            infer_pct = (now_price - infer) / last_price * 100
            pred_pct = (None if pred is None else (now_price - pred) / last_price * 100 )

            threshold = 0.1

            # print(forecast_data.index[i], str(round(now_price, 5)),
            #       '↓' if result_pct < -threshold else
            #       '↑' if threshold < result_pct else '→',
            #       round(result_price, 5), str(round(result_pct, 2)) + '%',
            #       '予測', round(infer, 5),
            #       '↓' if result_pct < 0 and infer_pct < -threshold else
            #       '↑' if 0 < result_pct and threshold < infer_pct else '×',
            #       str(round(infer_pct, 2)) + '%',
            #       '検証', '-' if pred is None else round(pred, 5),
            #       '-' if pred is None else
            #       '↓' if result_pct < 0 and pred_pct < -threshold else
            #       '↑' if 0 < result_pct and threshold < pred_pct else '×',
            #       '-' if pred is None else
            #       str(round(pred_pct, 2)) + '%',
            #       round(last_price, 5) != round(infer, 5)
            #       )

            forecast[i] = infer
        # print(len(np.array(list(forecast_data['test']))), len(forecast_data))
        # sim = model.simulate(np.array(list(forecast_data['test'])), nsimulations=len(forecast_data))
        # print(sim)
        forecast_data.loc[:, 'forecast'] = forecast[:len(forecast_data)]

        msg = 'ADF(' + str(round(ad_fuller_result[0], 7)) \
              + ') P-val(' + str(round(ad_fuller_result[1], 7)) \
              + ') RMSE(' + str(round(rmse_arima, 7)) + ')'

        com.log(msg + ' | Forecast(' + str(len(forecast_arima)) + ') ')
        print(forecast_arima)

        # チャートの表示定義
        fig1, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=cst.FIG_SIZE, sharex=True)
        fig1.suptitle(currency + '[' + str(split_len) + ' / ' + str(len(eq))
                      + '] ' + ('AUTO_' if 0 == str_pqd.count(',') else '') + 'ARIMA' + str(pdq)
                      + ' AIC(' + str(round(list(result_df['AIC'])[0], 7)) + ')'
                      + ' | ' + msg + ' 季節周期(' + str(span) + ')', fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(train_data, label='Actual', linewidth=1, color='blue')
        ax1.plot(advanced_decomposition.trend, label='Trend', linewidth=1, color='pink', linestyle='dashed')

        ax1.plot(forecast_data['test'], linewidth=1, color='blue')
        ax1.plot(pred_data['predict'], label='Predict', linewidth=1)
        ax1.plot(forecast_data['forecast'], label='Forecast', linewidth=1)

        ax2.plot(advanced_decomposition.seasonal, label='季節性', linewidth=1)
        ax2.plot(advanced_decomposition.resid, label='残差', linewidth=1)
        ax2.plot(eq_diff, label='対数差分', linewidth=1)

        fig1.autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(df) + len(df_future), step=((len(df) + len(df_future)) / 10)))
        ax1.legend(ncol=4, loc='upper left')
        ax2.legend(ncol=3, loc='upper left')
        plt.grid()
        plt.grid()

        # 表示の実行
        window.close()
        plt.show()

    finally:
        try: window.close()
        except: pass

    com.log('ARIMAモデル作成完了(' + com.conv_time_str(total_time) + ')')

def load(path):
    # モデルの読み込み
    loaded_result = ARIMAResults.load(path)

    # 読み込んだモデルで予測を実行
    # forecast = loaded_result.forecast(steps=10)
    # print(loaded_result.summary())
    # print(loaded_result.params)
    # print(list(loaded_result.model.data.row_labels)[-10:])
    # print(forecast)

def _optimize_Arima(data, str_pqd):

    if 0 == str_pqd.count(','):
        ps = range(0, 4)
        # d = range(0, 2)
        d = range(1, 2)
        qs = range(0, 4)
        order_list = list(product(ps, d, qs))
    else:
        str_pqd = str_pqd.split(',')
        ps = int(str_pqd[0])
        d = int(str_pqd[1])
        qs = int(str_pqd[2])
        order_list = [(ps, d, qs)]

    results = []
    for order in order_list:
        try:
            model = SARIMAX(data, order=(order[0], order[1], order[2])).fit(disp=False)
        except: continue

        aic = model.aic
        results.append([order, aic])

    if 0 == len(results): return None, None

    result_df = pd.DataFrame(results)
    result_df.columns = ['(p,d,q)', 'AIC']

    return result_df, model

## テストデータの株価を指定日数ごとに分けて小分けに予測する。
def rolling_forecast(df, train_len, test_len, interval, pdq):

    total_len = train_len + test_len
    pred_arima = []
    ## トレーニングデータ以降を始点としてテストデータをintervalで指定した数ごとに分けてループする。
    for i in range(train_len, total_len, interval):
        model = SARIMAX(df[:i], order=pdq).fit(disp=False)
        predictions = model.get_prediction(0, i + interval - 1)
        oos_pred = predictions.predicted_mean.iloc[-interval:]
        pred_arima.extend(oos_pred)

    return pred_arima

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
