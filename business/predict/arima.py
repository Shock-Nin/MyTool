#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

from tensorflow.python.util.numpy_compat import np_array

from common import com
from const import cst

import numpy as np
import pandas as pd
import FreeSimpleGUI as sg

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.ar_model import AutoReg

import joblib
from math import sqrt
from itertools import product

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

import warnings
warnings.simplefilter(action='ignore')

SAVE_PATH = f'{cst.MODEL_PATH[cst.PC]}models/'

def optimize_Arima(currency, df, pdq):
    com.log(f'AUTO_ARIMAチューニング開始')

    # AUTO_ARIMAのPDQリスト作成
    orders = list(product(pdq, pdq, pdq))

    # 保存パス
    save_path = f'{SAVE_PATH}ARIMA/Analytics/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    start_time = com.time_start()
    try:
        # 基本データからデータ作成
        eq = df.rename(columns={'Close': currency})
        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(eq.filter([currency]).values)

        # ARIMAのPDQ設定
        results = []

        window = com.progress(f'AUTO_ARIMAチューニング中', [currency, len(orders)], interrupt=True)
        event, values = window.read(timeout=0)

        for i in range(len(orders)):

            pdq = (int(orders[i][0]), int(orders[i][1]), int(orders[i][2]))
            try:
                window[currency].update(
                    f'{currency}[{com.conv_time_str(total_time)}] {str(pdq)} {str(i)} / {str(len(orders))}')
                window[currency + '_'].update(i)

                if 0 == i % 2:
                    com.log(f'AUTO_ARIMA[{com.conv_time_str(total_time)}] {str(i)} / {str(len(orders))}')
                # model = _create_model(scaled_data, 'SARIMA', pdq, pdqs)
                model = _create_model(scaled_data, 'ARIMA', pdq)

                results.append([pdq, model.aic, model.bic, model.hqic])
                model.remove_data()
            except:
                continue

            run_time = com.time_end(start_time)
            start_time = com.time_start()
            total_time += run_time

            # 中断イベント
            if _is_interrupt(window, event):
                return

        result_df = pd.DataFrame(results)
        result_df.columns = ['(p,d,q)', 'AIC', 'BIC', 'HQIC']

        # AIC低い順でソート、PDQの抽出
        result_df = result_df.sort_values(by='AIC')
        pdq = list(result_df['(p,d,q)'])[0]

        model = _create_model(scaled_data, 'ARIMA', pdq)

        msg = '\n'
        result_df = result_df.reset_index(drop=True)
        for i in range(len(result_df)):
            result_df.at[i, '(p,d,q)'] = \
                str(result_df.at[i, '(p,d,q)']).replace(' ', '')
            msg += f'\n{str(i)}: {result_df.at[i, '(p,d,q)']} | {result_df.at[i, 'AIC']}, {result_df.at[i, 'BIC']}, {result_df.at[i, 'HQIC']}'

        msg = f'\n\n{str(model.summary())}{msg}'
        window.close()
        model.remove_data()

        # モデル情報の保存
        path = f'{save_path}_{currency}_AUTO_ARIMA.txt'
        with open(path, 'w') as f:
            f.write(f'実行時間: {com.conv_time_str(total_time)} [{df.index[0][:4]} - {df.index[-1][:4]}]{msg}')

        com.dialog(f'AUTO_ARIMAチューニングが完了、保存しました。\n{com.conv_time_str(total_time)}',
                   f'AUTO_ARIMAチューニング')
        subprocess.Popen([cst.TXT_APP_PATH[cst.PC], path], shell='Win' == cst.PC)

    finally:
        try:
            window.close()
        except:
            pass

    return

def optimize_Ar(currency, df, lag):
    com.log(f'AutoRegチューニング開始')

    # AutoRegのラグリスト作成
    orders = list(product(lag))

    # 保存パス
    save_path = f'{SAVE_PATH}ARIMA/Analytics/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    start_time = com.time_start()
    try:
        # 基本データからデータ作成
        eq = df.rename(columns={'Close': currency})
        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(eq.filter([currency]).values)

        # ARのラグ設定
        results = []

        window = com.progress(f'AutoRegチューニング中', [currency, len(orders)], interrupt=True)
        event, values = window.read(timeout=0)

        for i in range(len(orders)):
            try:
                window[currency].update(
                    f'{currency}[{com.conv_time_str(total_time)}] {str(orders[i][0])} {str(i)} / {str(len(orders))}')
                window[currency + '_'].update(i)

                if 0 == i % 5:
                    com.log(f'AutoReg[{com.conv_time_str(total_time)}] {str(i)} / {str(len(orders))}')
                model = _create_model(scaled_data, 'AutoReg', int(orders[i][0]))

                results.append([int(orders[i][0]), model.aic, model.bic, model.hqic])
                model.remove_data()
            except:
                continue

            run_time = com.time_end(start_time)
            start_time = com.time_start()
            total_time += run_time

            # 中断イベント
            if _is_interrupt(window, event):
                return None

        result_df = pd.DataFrame(results)
        result_df.columns = ['lag', 'AIC', 'BIC', 'HQIC']

        # AIC低い順でソート、ラグの抽出
        result_df = result_df.sort_values(by='AIC')
        lag = list(result_df['lag'])[0]

        model = _create_model(scaled_data, 'AutoReg', lag)

        msg = '\n'
        result_df = result_df.reset_index(drop=True)
        for i in range(len(result_df)):
            result_df.at[i, 'lag'] = \
                str(result_df.at[i, 'lag']).replace('[', '').replace(']', '').replace(' ', '')
            msg += f'\n{str(i)}: {result_df.at[i, 'lag']} | {result_df.at[i, 'AIC']}, {result_df.at[i, 'BIC']}, {result_df.at[i, 'HQIC']}'
        msg = f'\n\n{str(model.summary())}{msg}'
        window.close()
        model.remove_data()

        # モデル情報の保存
        path = f'{save_path}_{currency}_AutoReg.txt'
        with open(path, 'w') as f:
            f.write(f'実行時間: {com.conv_time_str(total_time)} [{df.index[0][:4]} - {df.index[-1][:4]}]{msg}')
        com.dialog(f'AutoRegチューニングが完了、保存しました。\n{com.conv_time_str(total_time)}', f'AutoRegチューニング')
        subprocess.Popen([cst.TXT_APP_PATH[cst.PC], path], shell='Win' == cst.PC)

    finally:
        try: window.close()
        except: pass

    return

def run(currency, df, forecast, interval, str_pdq, lag, loaded_result=None):
# def run(currency, df, forecast, simu_try, simu_height, str_pdq, lag, loaded_result=None, ar_only=False):
    com.log(f'ARIMAモデル予測開始')

    # 保存パス
    save_path = f'{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'
    model_path = f'{SAVE_PATH}ARIMA/Model/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        # 基本データからデータ作成
        df_all = df.copy()
        forecast = int(np.round(forecast / 10) * 10)
        df = df[:-forecast]

        df_all = df_all.rename(columns={'Close': currency})
        eq = df.rename(columns={'Close': currency})

        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df_all.filter([currency]).values)

        pdq = str_pdq.split(',')
        if 3 == len(pdq):
            pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))

        # 学習・テストデータ作成
        split_len = int(np.ceil(len(eq)))
        train_data = scaled_data[:split_len].copy()
        test_data = df_all[currency][split_len:].copy()

        window = com.progress('モデル予測中', [currency, 2], interrupt=True)
        event, values = window.read(timeout=0)
        window[currency].update(f'{currency} ARモデル予測中')
        window[currency + '_'].update(0)

        # # 呼び出しモデルがなければ、作成
        # if loaded_result is None:
        #     model = _create_model(train_data, 'AutoReg', lag)
        #     joblib.dump(model, f'{model_path}_{currency}_AR({str(lag)}).pkl')
        #
        # # 呼び出しモデルがあれば、そのまま利用
        # else:
        #     model = loaded_result
        #     model.append(test_data)
        #     # model.append(scaled_data[split_len:])

        if loaded_result is None:
            # 予測データ作成
            refit_predictions = np.array([])
            actual_predictions = np.array([])
            refit_data = scaled_data[:split_len].copy()
            actual_data = scaled_data[:split_len].copy()

            refit_summaries = [[], [], [], [], []]
            actual_summaries = [[], [], [], [], []]

            train_start = 0
            for i in range(split_len, len(df_all), interval):

                refit_prediction, refit_summary = _predict_model(refit_data, 'AutoReg', lag, i, interval)
                actual_prediction, actual_summary = _predict_model(actual_data, 'AutoReg', lag, i, interval)

                refit_predictions = np.append(refit_predictions, np_array(refit_prediction))
                actual_predictions = np.append(actual_predictions, np_array(actual_prediction))

                for k in range(4):
                    refit_summaries[k].append(refit_summary[k])
                    actual_summaries[k].append(actual_summary[k])

                train_start += interval

                refit_data = np.append(refit_data[train_start: split_len], refit_predictions)
                actual_data = scaled_data[train_start: i + interval]

            refit_predictions = np.reshape(refit_predictions, (refit_predictions.shape[0], 1))
            actual_predictions = np.reshape(actual_predictions, (actual_predictions.shape[0], 1))

            predict_data = pd.DataFrame({'test': test_data})
            predict_data.loc[:, 'refit'] = scaler.inverse_transform(refit_predictions)
            predict_data.loc[:, 'actual'] = scaler.inverse_transform(actual_predictions)

            refit_summaries = [float(round(np.mean(refit_summaries[k]), 5)) for k in range(4)] \
                + [round(sqrt(mean_squared_error(predict_data['test'], predict_data['refit'])), 5)]

            actual_summaries = [float(round(np.mean(actual_summaries[k]), 5)) for k in range(4)] \
                + [round(sqrt(mean_squared_error(predict_data['test'], predict_data['actual'])), 5)]

            model_prediction, model_summary = _predict_model(train_data, 'AutoReg', lag, split_len, forecast,
                                                             f'{model_path}_{currency}_AR({str(lag)})')
            model_predictions = np_array(model_prediction)

            model_predictions = np.reshape(model_predictions, (model_predictions.shape[0], 1))
            predict_data.loc[:, 'normal'] = scaler.inverse_transform(model_predictions)

            model_summaries = [round(np.mean(model_summary[k]), 5) for k in range(4)] \
                + [round(sqrt(mean_squared_error(predict_data['test'], predict_data['normal'])), 5)]

            ar_summary = [model_summaries[-1],
                          'Type: [Normal, Refit, Predict]\n' + '\n'.join(
                              [['AIC', 'BIC', 'HQIC', 'BSE', 'RMSE'][k] + ': ['
                               + f'{model_summaries[k]}, {refit_summaries[k]}, {actual_summaries[k]}]'
                               for k in range(5)])]

        # 中断イベント
        if _is_interrupt(window, event):
            return None




        run_time = com.time_end(start_time)
        com.log('ARモデル完了(' + com.conv_time_str(run_time) + ') ')

        window.close()

        # ARIMAモデル
        window = com.progress('モデル予測中', [currency, 2], interrupt=True)
        event, values = window.read(timeout=0)
        window[currency].update(f'{currency} ARIMAモデル予測中')
        window[currency + '_'].update(1)

        # # 呼び出しモデルがなければ、作成して保存
        # if loaded_result is None:
        #     model = _create_model(train_data, 'ARIMA', pdq)
        #     # モデルの保存
        #     joblib.dump(model, f'{model_path}_{currency}_ARIMA({str_pdq}).pkl')
        #
        #     run_time = com.time_end(start_time)
        #     com.log('ARIMAモデル作成・保存完了(' + com.conv_time_str(run_time) + ') ')
        #
        # # 呼び出しモデルがあれば、そのまま利用
        # else:
        #     model = loaded_result
        #     print(test_data)
        #     model.append(test_data)

        if loaded_result is None:
            # 予測データ作成
            refit_predictions = np.array([])
            actual_predictions = np.array([])
            refit_data = scaled_data[:split_len].copy()
            actual_data = scaled_data[:split_len].copy()

            refit_summaries = [[], [], [], [], []]
            actual_summaries = [[], [], [], [], []]

            train_start = 0
            for i in range(split_len, len(df_all), interval):

                refit_prediction, refit_summary = _predict_model(refit_data, 'ARIMA', pdq, i, interval)
                actual_prediction, actual_summary = _predict_model(actual_data, 'ARIMA', pdq, i, interval)

                refit_predictions = np.append(refit_predictions, np_array(refit_prediction))
                actual_predictions = np.append(actual_predictions, np_array(actual_prediction))

                for k in range(4):
                    refit_summaries[k].append(refit_summary[k])
                    actual_summaries[k].append(actual_summary[k])

                train_start += interval

                refit_data = np.append(refit_data[train_start: split_len], refit_predictions)
                actual_data = scaled_data[train_start: i + interval]

            refit_predictions = np.reshape(refit_predictions, (refit_predictions.shape[0], 1))
            actual_predictions = np.reshape(actual_predictions, (actual_predictions.shape[0], 1))

            forecast_data = pd.DataFrame({'test': test_data})
            forecast_data.loc[:, 'refit'] = scaler.inverse_transform(refit_predictions)
            forecast_data.loc[:, 'actual'] = scaler.inverse_transform(actual_predictions)

            refit_summaries = [float(round(np.mean(refit_summaries[k]), 5)) for k in range(4)] \
                              + [round(sqrt(mean_squared_error(forecast_data['test'], forecast_data['refit'])), 5)]

            actual_summaries = [float(round(np.mean(actual_summaries[k]), 5)) for k in range(4)] \
                               + [round(sqrt(mean_squared_error(forecast_data['test'], forecast_data['actual'])), 5)]

            model_prediction, model_summary = _predict_model(train_data, 'AutoReg', lag, split_len, forecast,
                                                             f'{model_path}_{currency}_AR({str(pdq)})')
            model_predictions = np_array(model_prediction)

            model_predictions = np.reshape(model_predictions, (model_predictions.shape[0], 1))
            forecast_data.loc[:, 'normal'] = scaler.inverse_transform(model_predictions)

            model_summaries = [round(np.mean(model_summary[k]), 5) for k in range(4)] \
                              + [round(sqrt(mean_squared_error(forecast_data['test'], forecast_data['normal'])), 5)]

            arima_summary = [model_summaries[-1],
                             'Type: [Normal, Refit, Predict]\n' + '\n'.join(
                                 [['AIC', 'BIC', 'HQIC', 'BSE', 'RMSE'][k] + ': ['
                                  + f'{model_summaries[k]}, {refit_summaries[k]}, {actual_summaries[k]}]'
                                  for k in range(5)])]

            window.close()

        msg = ', '.join([msg for msg in [f'ARIMA: ({str_pdq.replace(',', ' ')})', f'AR({str(lag)})'] if '' != msg])

        # チャートの表示定義
        fig1, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=cst.FIG_SIZE, sharex=True)
        fig1.suptitle(f'{currency}[{df.index[0][:4]} - {df.index[-1][:4]}] {msg.replace('\n', '')}', fontsize=cst.FIG_FONT_SIZE)
        ax1.plot(df_all, linewidth=1, color='blue', alpha=0.3)

        ax1.plot(forecast_data['normal'], label='ARIMA', linewidth=1, alpha=0.5)
        ax1.plot(forecast_data['refit'], label='ARIMA(Refit)', linewidth=1, alpha=0.5)
        ax1.plot(forecast_data['actual'], label='ARIMA(Predict)', linewidth=1, alpha=0.5)
        # ax1.plot(forecast_data['normal'], label='ARIMA', linewidth=1, color='green', alpha=0.5)
        # ax1.plot(forecast_data['refit'], label='ARIMA(Refit)', linewidth=1, color='orange', alpha=0.5)
        # ax1.plot(forecast_data['actual'], label='ARIMA(Predict)', linewidth=1, color='red', alpha=0.5)

        ax1.plot(predict_data['normal'], label='AR', linewidth=1, alpha=0.5)
        ax1.plot(predict_data['refit'], label='AR(Refit)', linewidth=1, alpha=0.5)
        ax1.plot(predict_data['actual'], label='AR(Predict)', linewidth=1, alpha=0.5)
        # ax1.plot(predict_data['normal'], label='AR', linewidth=1, color='green', alpha=0.5)
        # ax1.plot(predict_data['refit'], label='AR(Refit)', linewidth=1, color='orange', alpha=0.5)
        # ax1.plot(predict_data['actual'], label='AR(Predict)', linewidth=1, color='red', alpha=0.5)

        fig1.autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(df_all), step=(len(df_all) / 10)))
        ax1.legend(ncol=6, loc='upper left')
        plt.grid()
        plt.grid()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log('ARIMAモデル予測完了(' + com.conv_time_str(total_time) + ')')

        # モデル情報の保存
        file_name = f'_ARIMA({str_pdq})_AR({str(lag)})'
        save_path = f'{SAVE_PATH}ARIMA/{'Analytics' if loaded_result is None else 'Result'}/{save_path}_{currency}{file_name}'

        with open(f'{save_path}.txt', 'w') as f:
            f.write(f'学習時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}] '
                    + f'予測期間: {str(forecast)}, '
                    + f'予測間隔: {str(interval)}\n{msg}\n{arima_summary[0]}\n{ar_summary[0]}\n'
                    + '--------------------------------------------------------------------\n'
                    + f'{arima_summary[1]}\n{ar_summary[1]}')
        plt.savefig(f'{save_path}.png',  format='png')
        subprocess.Popen([cst.TXT_APP_PATH[cst.PC], f'{save_path}.txt'], shell='Win' == cst.PC)
        # 表示の実行
        plt.show()

    finally:
        try: window.close()
        except: pass

def _predict_model(df, arima_type, prm, cnt, interval, model_path=None):

        model = _create_model(df, arima_type, prm, model_path)
        prediction = model.predict(cnt, cnt + interval - 1)
        summary = [model.aic, model.bic, model.hqic, model.bse, model.summary]
        model.remove_data()

        return prediction, summary

def _create_model(df, arima_type, pdq, model_path):
    try:
        if 'AutoReg' == arima_type:
            model = AutoReg(df, lags=pdq).fit()
        else:
            model = ARIMA(df, order=pdq).fit()
        # elif 'SARIMA' == arima_type:
            # model = SARIMAX(df, order=pdq, seasonal_order=(1, 1, 1, 130)).fit(disp=False)
            # model = SARIMAX(df, order=pdq, seasonal_order=pdqs).fit(disp=False)
            # model = pm.auto_arima(df,
            #                       start_p=pdq[0], d=pdq[1], start_q=pdq[2], max_p=pdq[0], max_d=pdq[1], max_q=pdq[2],
            #                       start_P=pdqs[0], D=pdqs[1], start_Q=pdqs[2], max_P=pdqs[0], max_D=pdqs[1], max_Q=pdqs[2],
            #                       m=pdqs[3], seasonal=True)
    except Exception as e:
        com.log(f'ARIMAモデル作成失敗: {str(pdq)} | {str(e)}', lv='W')
        return None
    if model_path is not None:
        # モデルの保存
        joblib.dump(model, f'{model_path}.pkl')
    return model

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
