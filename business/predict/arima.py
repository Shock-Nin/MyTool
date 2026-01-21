#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

from common import com
from const import cst

import numpy as np
import pandas as pd
import FreeSimpleGUI as sg

from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.ar_model import AutoReg

from itertools import product
from sklearn.metrics import mean_squared_error
from math import sqrt

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import warnings
warnings.simplefilter(action='ignore')

SAVE_PATH = f'{cst.MODEL_PATH[cst.PC]}models/'

# AUTO_ARIMAのPDQリスト作成
ORDERS = list(product(range(1, 3), range(1, 3), range(1, 3),
                      range(1, 3), range(1, 3), range(1, 3),
                      [10, 25, 50, 75, 100, 150]))

def optimize_Arima(currency, df):
    com.log(f'AUTO_ARIMAチューニング開始')

    # 保存パス
    save_path = f'{SAVE_PATH}ARIMA/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        # 基本データからデータ作成
        eq = df.rename(columns={'Close': currency})
        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(eq.filter([currency]).values)

        # ARIMAのPDQ設定
        results = []

        window = com.progress(f'AUTO_ARIMAチューニング中', [currency, len(ORDERS)], interrupt=True)
        event, values = window.read(timeout=0)

        for i in range(len(ORDERS)):

            pdq = (ORDERS[i][0], ORDERS[i][1], ORDERS[i][2])
            pdqs = (ORDERS[i][3], ORDERS[i][4], ORDERS[i][5], ORDERS[i][6])

            try:
                window[currency].update(f'{currency} {str(pdq)}{str(pdqs)} {str(i)} / {str(len(ORDERS))}')
                window[currency + '_'].update(i)

                if 0 == i % 2:
                    com.log(f'AUTO_ARIMA {str(i)} / {str(len(ORDERS))}')
                model = _create_model(scaled_data, 'SARIMA', pdq, pdqs)

                aic = model.aic
                results.append([[pdq, pdqs], aic])
                model.remove_data()
            except:
                continue

            # 中断イベント
            if _is_interrupt(window, event):
                return

            if 0 == len(results): continue

        result_df = pd.DataFrame(results)
        result_df.columns = ['(p,d,q)(p,q,d,s)', 'AIC']

        # AIC低い順でソート、PDQの抽出
        result_df = result_df.sort_values(by='AIC')
        pdq = list(result_df['(p,d,q)(p,q,d,s)'])[0]
        pdqs = pdq[1]
        pdq = pdq[0]

        model = _create_model(scaled_data, 'SARIMA', pdq, pdqs)

        msg = '\n'
        result_df = result_df.reset_index(drop=True)
        for i in range(len(result_df)):
            result_df.at[i, '(p,d,q)(p,q,d,s)'] = \
                str(result_df.at[i, '(p,d,q)(p,q,d,s)']).replace('[', '').replace(']', '').replace(' ', '')
            msg += f'\n{result_df.at[i, '(p,d,q)(p,q,d,s)']}'
        msg = f'\n\n{str(model.summary())}{msg}'
        window.close()
        model.remove_data()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(f'AUTO_ARIMAチューニング完了({com.conv_time_str(run_time)})')

        # モデル情報の保存
        path = f'{save_path}_{currency}_AUTO_ARIMA.txt'
        with open(path, 'w') as f:
            f.write(f'実行時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}]{msg}')

        com.dialog(f'AUTO_ARIMAチューニングが完了、保存しました。\n{com.conv_time_str(run_time)}', f'AUTO_ARIMAチューニング')
        subprocess.Popen([cst.TXT_APP_PATH[cst.PC], path], shell='Win' == cst.PC)

    finally:
        try: window.close()
        except: pass

    return

def run(currency, df, forecast, simu_try, simu_height, str_pdq, str_pdqs, lag, loaded_result=None, ar_only=False):
    com.log(f'ARIMAモデル予測開始')

    # 保存パス
    save_path = f'{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'
    model_path = f'{SAVE_PATH}ARIMA/Model/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        # 基本データからデータ作成
        df_all = df.copy()
        df = df[:-forecast]

        df_all = df_all.rename(columns={'Close': currency})
        eq = df.rename(columns={'Close': currency})

        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df_all.filter([currency]).values)

        pdq = str_pdq.split(',')
        if 3 == len(pdq):
            pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))
        pdqs = str_pdqs.split(',')
        if 4 == len(pdqs):
            pdqs = (int(pdqs[0]), int(pdqs[1]), int(pdqs[2]), int(pdqs[3]))

        # 学習データ作成
        split_len = int(np.ceil(len(eq)))

        train_data = scaled_data[:split_len]
        # test_data = df_all[currency][split_len:]

        # テストデータ作成
        # test_data = scaled_data[split_len:]
        test_data = df_all[currency][split_len:]

        # valid = df_all[currency][split_len:]



        # train_data = scaled_data[0: split_len, :]
        # x_train = []
        # for i in range(len(train_data)):
        #     x_train.append(train_data[i: i, 0])
        # x_train = np.array(train_data)
        # train_data = np.reshape(np.array(train_data), (np.array(train_data).shape[0], 1))



        # if '-' != interval:

        window = com.progress('ARIMAモデル予測中', [currency, 0], interrupt=True)
        event, values = window.read(timeout=0)

        # # トレーニングデータ以降を始点としてテストデータをintervalで指定した数ごとに分けてループする。
        # for i in range(train_len, total_len, interval):

        # window[currency].update(f'{currency} Predict ({str(int((i - train_len) / interval))} / {str(int(test_len / interval))})')
        # window[currency + '_'].update(int((i - train_len) / interval))
        #
        # if 0 == int((i - train_len) / interval) % 10:
        #     com.log(f'Predict: {str(int((i - train_len) / interval))} / {str(int(test_len / interval))}')

        # 呼び出しモデルがなければ、作成
        if loaded_result is None:
            model = _create_model(train_data, 'AR', lag, '')
            model.save(f'{model_path}_{currency}_AR({str(lag)}).pkl')

        # 呼び出しモデルがあれば、そのまま利用
        else:
            model = loaded_result
            model.append(train_data)

        # predictions = model.predict(split_len, len(scaled_data) - 1)
        predictions = model.forecast(steps=forecast)

        model_summary = '\n' + str(model.summary())
        model.remove_data()

        # 中断イベント
        if _is_interrupt(window, event):
            return None

        predictions = np.array(predictions)
        predictions = np.reshape(predictions, (predictions.shape[0], 1))

        # valid['predictions'] = scaler.inverse_transform(predictions)
        # print(valid)

        predict_data = pd.DataFrame({'test': test_data})
        predict_data.loc[:, 'predict'] = scaler.inverse_transform(predictions)



        # predict_data = scaled_data
        #
        # new_predictions = []
        # for prediction in predictions:
        #     new_predictions.append(np.array(prediction))
        #
        # print(len(predict_data), len(predict_data[-split_len:]), len(predictions), predict_data, np.array(predictions))
        # predict_data = predict_data[-split_len:] + np.array(new_predictions)

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('ARモデル完了(' + com.conv_time_str(run_time) + ') ')

        window.close()

        # SARIMAモデル
        if not ar_only and 3 == len(pdq):
            window = com.progress('ARIMAモデル予測中', [currency, simu_try], interrupt=True)
            event, values = window.read(timeout=0)
            window[currency].update(f'{currency} シミュレーション 0 / {str(simu_try)}')

            # 呼び出しモデルがなければ、作成して保存
            if loaded_result is None:
                model = _create_model(train_data, 'SARIMA', pdq, pdqs)
                # モデルの保存
                model.save(f'{model_path}_{currency}_SARIMA({str_pdq})({str_pdqs}).pkl')
            # 呼び出しモデルがあれば、そのまま利用
            else:
                model = loaded_result

            # 予測データ作成
            forecast_data = pd.DataFrame({'test': test_data})

            # シミュレーションの実行
            simulations = []
            for i in range(simu_try):
                window[currency].update(f'{currency} シミュレーション {str(i)} / {str(simu_try)}')
                window[currency + '_'].update(i)

                if 0 == i % 100:
                    com.log(f'シミュレーション: {str(i)} / {str(simu_try)}')

                sim = model.simulate(nsimulations=len(forecast_data), anchor='end')
                simulations.append(sim)

                # 中断イベント
                if _is_interrupt(window, event):
                    return None

            model_summary = '\n' + str(model.summary()) + model_summary
            model.remove_data()

            forecast_median = np.median(simulations, axis=0)
            forecast_percentiles = np.percentile(simulations, [simu_height, 100 - simu_height], axis=0)

            forecast_data.loc[:, 'forecast_upper'] = forecast_percentiles[1]
            forecast_data.loc[:, 'forecast_lower'] = forecast_percentiles[0]
            forecast_data.loc[:, 'forecast_median'] = forecast_median

            window.close()

        msg = ', '.join([msg for msg in [
            (f'SARIMA: ({str_pdq.replace(',', ' ')})({str_pdqs.replace(',', ' ')})' if not ar_only and 3 == len(pdq) else ''),
            f'AR({str(lag)})'] if '' != msg])

        # チャートの表示定義
        fig1, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=cst.FIG_SIZE, sharex=True)
        fig1.suptitle(f'{currency}[{df.index[0][:4]} - {df.index[-1][:4]}] {msg.replace('\n', '')}', fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(df_all, label='Actual', linewidth=1, color='blue', alpha=0.3)
        ax1.plot(predict_data['predict'], label='AR', linewidth=1, color='red', alpha=0.5)

        if not ar_only and 3 == len(pdq):
            ax1.fill_between(np.arange(split_len, split_len + len(forecast_data['forecast_median']), 1),
                             forecast_data['forecast_upper'], forecast_data['forecast_lower'], color='orange', alpha=0.2)
            ax1.plot(forecast_data['forecast_median'], label='SARIMA', linewidth=1, color='green', alpha=0.5)

        fig1.autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(df_all), step=(len(df_all) / 10)))
        ax1.legend(ncol=5, loc='upper left')
        plt.grid()
        plt.grid()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('ARIMAモデル予測完了(' + com.conv_time_str(total_time) + ')')

        # モデル情報の保存
        if not ar_only and 3 == len(pdq):
            file_name = f'_SARIMA({str_pdq})({str_pdqs})_AR({str(lag)})'
            save_path = f'{SAVE_PATH}ARIMA/{'Analytics' if loaded_result is None else 'Result'}/{save_path}_{currency}{file_name}'

            with open(f'{save_path}.txt', 'w') as f:
                f.write(f'学習時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}] '
                        + f'予測期間: {str(forecast)}, '
                        + f'シミュレーション: {str(simu_try)}, バンド幅: {str(simu_height)}'
                        + f'\n{msg}\n{model_summary}')
            plt.savefig(f'{save_path}.png',  format='png')
            subprocess.Popen([cst.TXT_APP_PATH[cst.PC], f'{save_path}.txt'], shell='Win' == cst.PC)
        # 表示の実行
        plt.show()

    finally:
        try: window.close()
        except: pass

# def save(currency, df, str_pdq, str_pdqs, lag):
#     com.log('ARIMAモデル作成開始')
#
#     # モデルの保存
#     save_path = f'{SAVE_PATH}Model/ARIMA/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'
#
#     total_time = 0
#     try:
#         start_time = com.time_start()
#
#         window = com.progress('', [currency, 2], interrupt=True)
#         event, values = window.read(timeout=0)
#
#         # 基本データからデータ作成
#         eq = df.rename(columns={'Close': currency})
#         # データを0〜1の範囲に正規化
#         scaler = MinMaxScaler(feature_range=(0, 1))
#         scaled_data = scaler.fit_transform(eq.filter([currency]).values)
#
#         pdq = str_pdq.split(',')
#         pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))
#         pdqs = str_pdqs.split(',')
#         pdqs = (int(pdqs[0]), int(pdqs[1]), int(pdqs[2]), int(pdqs[3]))
#
#         arima_types = ['AR', 'SARIMA']
#         for i in range(len(arima_types)):
#             window[currency].update(f'{currency} {arima_types[i]} モデル作成中')
#             window[currency + '_'].update(i)
#
#             com.log(f'ARIMAモデル作成中: {arima_types[i]} ')
#             model = _create_model(scaled_data, arima_types[i], (lag if 'AR' == arima_types[i] else pdq), pdqs)
#             model_name = (f'AR({str(lag)})' if 'AR' == arima_types[i] else f'SARIMA({str_pdq})({str_pdqs})')
#             model.save(f'{save_path}_{currency}_{model_name}.pkl')
#
#             # 中断イベント
#             if _is_interrupt(window, event):
#                 return None
#
#         window.close()
#
#         run_time = com.time_end(start_time)
#         total_time += run_time
#         com.log(f'ARIMAモデル作成完了({com.conv_time_str(run_time)})')
#         com.dialog(f'ARIMAモデル作成が完了、保存しました。\n{com.conv_time_str(run_time)}', 'ARIMAモデル作成', )
#
#     finally:
#         try: window.close()
#         except: pass

def _create_model(df, arima_type, pdq, pdqs=None):
    try:
        if 'AR' == arima_type:
            model = AutoReg(df, lags=pdq).fit()
        elif 'SARIMA' == arima_type:
            model = SARIMAX(df, order=pdq, seasonal_order=pdqs).fit(disp=False)
        else:
            model = ARIMA(df, order=pdq).fit()
    except:
        com.log(f'ARIMAモデル作成失敗: {str(pdq)}' + ('' if pdqs is None else f', {str(pdqs)}'), lv='W')
        return None

    return model

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
