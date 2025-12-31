#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import math
import os

from soupsieve.util import lower

from common import com
from const import cst

import numpy as np
import statistics
import pandas as pd
import FreeSimpleGUI as sg

from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.ar_model import AutoReg
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

SAVE_PATH = f'{cst.HST_PATH[cst.PC].replace('\\', '/').replace('history', 'models/')}'

# ARIMAのPDQリスト作成
ORDERS = list(product(range(1, 6), range(1, 3), range(1, 6)))

def optimize_Arima(currency, df, span):
    com.log('AUTO_ARIMA取得開始')

    # 保存パス
    save_path = f'{SAVE_PATH}Optimize/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        # 基本データからデータ作成
        df_seasonal = df.copy().rename(columns={'Close': currency})
        eq = df.rename(columns={'Close': currency})

        # 季節性・残差・対数差分の取得
        advanced_decomposition = STL(df_seasonal[currency], period=span, robust=True).fit()
        eq_diff = np.diff(df_seasonal[currency], n=1)
        ad_fuller_result = adfuller(eq_diff)

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(f'季節性取得完了({com.conv_time_str(run_time)})')

        # ARIMAのPDQ設定
        result_dfs = []
        msg = f'季節周期: {str(span)}, ADF: {str(round(ad_fuller_result[0], 7))}, P-val: {str(round(ad_fuller_result[1], 7))}\n'
        for pqd_type in ['', 'S']:
            results = []

            window = com.progress('AUTO_ARIMA(S)定義中', [currency, len(ORDERS)], interrupt=True)
            event, values = window.read(timeout=0)

            for i in range(len(ORDERS)):

                if 'S' == pqd_type:
                    window[currency].update(f'{currency} {str(i)} / {str(len(ORDERS))}')
                    window[currency + '_'].update(i)

                    if 0 == i % 5:
                        com.log(f'{pqd_type} {str(i)} / {str(len(ORDERS))}')
                try:
                    model = _create_model(eq[currency], pqd_type, (ORDERS[i][0], ORDERS[i][1], ORDERS[i][2]), span)
                except:
                    continue
                aic = model.aic
                results.append([ORDERS[i], aic])

            # 中断イベント
            if _is_interrupt(window, event):
                return

            if 0 == len(results): continue

            result_df = pd.DataFrame(results)
            result_df.columns = ['(p,d,q)', 'AIC']

            # AIC低い順でソート、PDQの抽出
            result_df = result_df.sort_values(by='AIC')
            pdq = list(result_df['(p,d,q)'])[0]
            aic = list(result_df['AIC'])[0]

            model = _create_model(eq[currency], pqd_type, pdq, span)
            result_dfs.append([pqd_type, pdq, aic, result_df])

            msg += f'\n\n{pqd_type} {str(result_df)}\n\n{model.summary().as_text()}\n\n{str(ad_fuller_result)}\n'

            window.close()

        # チャートの表示定義
        fig1, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=cst.FIG_SIZE,
                                        gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        fig1.suptitle(f'AUTO_ARIMA: {currency}[{str(len(eq))}]', fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(df_seasonal, label='Actual', linewidth=1, color='blue', alpha=0.3)
        ax1.plot(advanced_decomposition.trend, ':', label='Trend', linewidth=1, color='pink', alpha=0.5)

        ax2.plot(advanced_decomposition.seasonal, label='季節性(' + str(span) + ')', linewidth=1, alpha=0.5)
        ax2.plot(advanced_decomposition.resid, label='残差', linewidth=1, alpha=0.2)
        ax2.plot(eq_diff, '.', label='対数差分', linewidth=1, alpha=0.2)

        fig1.autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(df), step=((len(df)) / 10)))
        ax1.legend(ncol=2, loc='upper left')
        ax2.legend(ncol=3, loc='upper left')
        plt.grid()
        plt.grid()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(f'AUTO_ARIMA取得完了({com.conv_time_str(run_time)})')

        # モデル情報の保存
        with open(f'{save_path}_{currency}_ARIMA(PDQ).txt', 'a') as f:
            f.write(f'実行時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}]\n{msg}')
        plt.savefig(f'{save_path}_{currency}_ARIMA(PDQ).png', format='png')

        # 表示の実行
        plt.show()

    finally:
        try: window.close()
        except: pass

    return

def run(currency, df, span, forecast, interval, simu_try, simu_height, str_pdq, loaded_result=None):
    arima_type = 'S'
    com.log(f'ARIMAモデル予測開始')

    # 保存パス
    save_path = f'{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        # 基本データからデータ作成
        df_future = df.copy()[-forecast:]
        df_seasonal = df.copy()
        df = df[:-forecast]

        df_future = df_future.rename(columns={'Close': currency})
        df_seasonal = df_seasonal.rename(columns={'Close': currency})
        eq = df.rename(columns={'Close': currency})

        pdq = str_pdq.split(',')
        pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))

        # 学習データ作成
        split_len = int(np.ceil(len(eq)))
        train_data = eq[currency][:split_len]

        # テストデータを定義
        test_data = df_seasonal[currency][split_len:]
        train_len = len(train_data)
        test_len = len(test_data)
        total_len = train_len + test_len

        if loaded_result is None:
            predict_arima = []

            window = com.progress('ARIMAモデル予測中', ['Predict', int(test_len / interval)], interrupt=True)
            event, values = window.read(timeout=0)

            ## トレーニングデータ以降を始点としてテストデータをintervalで指定した数ごとに分けてループする。
            for i in range(train_len, total_len, interval):

                window['Predict'].update(f'{currency} Predict ({str(int((i - train_len) / interval))} / {str(int(test_len / interval))})')
                window['Predict_'].update(int((i - train_len) / interval))

                if 0 == int((i - train_len) / interval) % 5:
                    com.log(f'Predict: {str(int((i - train_len) / interval))} / {str(int(test_len / interval))}')

                model = _create_model(df[:i], arima_type, pdq, span)
                predictions = model.get_prediction(0, i + interval - 1)
                oos_pred = predictions.predicted_mean.iloc[-interval:]
                predict_arima.extend(oos_pred)

                # 中断イベント
                if _is_interrupt(window, event):
                    return None

            # 検証データ作成
            predict_data = pd.DataFrame({'test': test_data})
            predict_data.loc[:, 'predict'] = predict_arima[:len(predict_data)]

            # RMSE取得
            predict_rmse = sqrt(mean_squared_error(predict_data['test'], predict_data['predict']))

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log('Predict完了(' + com.conv_time_str(run_time) + ') ')

            window.close()

        window = com.progress('ARIMAモデル予測中', ['シミュレーション', simu_try], interrupt=True)
        event, values = window.read(timeout=0)

        # モデルで予測を実行
        if loaded_result is None:
            model = _create_model(train_data, arima_type, pdq, span)
        else:
            model = loaded_result

        if 'A' != arima_type:
            # 予測データ作成
            forecast_data = pd.DataFrame({'test': test_data})

            simulations = []
            for i in range(simu_try):

                window['シミュレーション'].update(f'シミュレーション {str(i)} / {str(simu_try)}')
                window['シミュレーション_'].update(i)

                if 0 == i % 100:
                    com.log(f'シミュレーション: {str(i)} / {str(simu_try)}')

                sim = model.simulate(nsimulations=len(test_data), anchor='end')
                simulations.append(sim)

                # 中断イベント
                if _is_interrupt(window, event):
                    return None

            forecast_median = np.median(simulations, axis=0)
            forecast_percentiles = np.percentile(simulations, [simu_height, 100 - simu_height], axis=0)

            forecast_data.loc[:, 'forecast_upper'] = forecast_percentiles[1]
            forecast_data.loc[:, 'forecast_lower'] = forecast_percentiles[0]
            forecast_data.loc[:, 'forecast_median'] = forecast_median

        msg = (f'\n\nARIMA: {str(pdq).strip().replace(',', '')}'
               + f', RMSE: {str(round(predict_rmse, 7))}' if loaded_result is None else '')

        # チャートの表示定義
        fig1, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=cst.FIG_SIZE, sharex=True)
        fig1.suptitle(currency + '[' + str(len(eq)) + ' - ' + str(forecast) + '] ' + msg, fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(df_seasonal, label='Actual', linewidth=1, color='blue', alpha=0.3)

        if loaded_result is None:
            ax1.plot(predict_data['predict'], label='Predict', linewidth=1, color='red', alpha=0.5)

        if 'A' != arima_type:
            ax1.fill_between(np.arange(split_len, split_len + len(forecast_data['forecast_median']), 1),
                             forecast_data['forecast_upper'], forecast_data['forecast_lower'], color='orange', alpha=0.2)
            ax1.plot(forecast_data['forecast_median'], label='Median', linewidth=1, color='green', alpha=0.3)

        fig1.autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(df) + len(df_future), step=((len(df) + len(df_future)) / 10)))
        ax1.legend(ncol=5, loc='upper left')
        plt.grid()
        plt.grid()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('ARIMAモデル予測完了(' + com.conv_time_str(total_time) + ')')

        # モデル情報の保存
        file_name = f'_ARIMA{str(pdq).replace(' ', '')}'
        file_name += ('Analytics' if loaded_result is None else '_Result')
        save_path = f'{SAVE_PATH}{'Analytics' if loaded_result is None else 'Result'}/{save_path}_{currency}{file_name}'

        with open(f'{save_path}.txt', 'w') as f:
            f.write(f'学習時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}]\n'
                    + f'季節周期: {str(span)}, 予測期間: {str(forecast)}, '
                    + (f'予測間隔: {str(interval)}, ' if loaded_result is None else '')
                    + f'シミュレーション: {str(simu_try)}, バンド幅: {str(simu_height)}'
                    + f'{msg}\n\n{model.summary().as_text()}\n\n'
                    + f'{str(model.params)}\n\n{str(model.bse)}\n\n{str(model.tvalues)}\n\n'
                    + f'{str(model.pvalues)}\n{str(model.conf_int())}')
        plt.savefig(f'{save_path}.png',  format='png')

        # 表示の実行
        window.close()
        plt.show()

    finally:
        try: window.close()
        except: pass

def save(currency, df, span, str_pdq):
    arima_type = 'S'
    com.log('ARIMAモデル作成開始')

    # モデルの保存
    save_path = f'{SAVE_PATH}Model/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        window = com.progress('', ['ARIMAモデル作成中', 1], interrupt=True)
        event, values = window.read(timeout=0)

        # 基本データからデータ作成
        eq = df.rename(columns={'Close': currency})
        pdq = str_pdq.split(',')
        pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))

        model = _create_model(eq, arima_type, pdq, span)
        model.save(f'{save_path}_{currency}_ARIMA{str(pdq).replace(' ', '')}.pkl')
        window.close()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(f'ARIMAモデル作成完了({com.conv_time_str(run_time)})')
        com.dialog(f'ARIMAモデル作成が完了、保存しました。\n{com.conv_time_str(run_time)}', 'ARIMAモデル作成', )

    finally:
        try: window.close()
        except: pass

def _create_model(df, arima_type, pdq, span):
    try:
        if 'A' == arima_type:
            model = AutoReg(df, lags=span).fit()
        elif 'S' == arima_type:
            # model = SARIMAX(df, order=pdq).fit(disp=False)
            model = SARIMAX(df, order=pdq, seasonal_order=(pdq[0], pdq[1], pdq[2], span)).fit(disp=False)
        else:
            model = ARIMA(df, order=pdq).fit()
    except:
        return None

    return model

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
