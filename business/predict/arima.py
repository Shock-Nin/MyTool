#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

from common import com
from const import cst

import numpy as np
import pandas as pd
import FreeSimpleGUI as sg
#
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.statespace.sarimax import SARIMAX

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
ORDERS_PDQS = list(product(range(0, 3), range(0, 3), range(0, 3)))

def optimize_Arima(currency, df, span, pdqs):
    com.log('AUTO_ARIMA取得開始')

    # 保存パス
    save_path = f'{SAVE_PATH}Optimize/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        # 基本データからデータ作成
        eq = df.rename(columns={'Close': currency})

        # ARIMAのPDQ設定
        result_dfs = []
        msg = ''

        for pqd_type in ['SARIMA', '']:
            results = []
            orders = (ORDERS_PDQS if pdqs and 'SARIMA' == pqd_type else ORDERS)

            window = com.progress(f'AUTO_ARIMA{'_S' if pdqs and 'SARIMA' == pqd_type else ''} 定義中', [currency, len(orders)], interrupt=True)
            event, values = window.read(timeout=0)

            for i in range(len(orders)):

                try:
                    if 'SARIMA' == pqd_type:
                        window[currency].update(f'{currency} {str(orders[i])} {str(i)} / {str(len(orders))}')
                        window[currency + '_'].update(i)

                        if 0 == i % (2 if pdqs else 5):
                            com.log(f'{pqd_type} {str(i)} / {str(len(orders))}')

                    if pdqs:
                        model = _create_model(eq[currency], pqd_type, (1, 1, 1), span, orders[i])
                    else:
                        model = _create_model(eq[currency], pqd_type, (orders[i][0], orders[i][1], orders[i][2]), span)

                    aic = model.aic
                    results.append([orders[i], aic])
                    model.remove_data()

                except:
                    continue

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

            msg += f'\n\n{pqd_type} {str(result_df)}\n\n{str(model.summary())}'
            window.close()
            model.remove_data()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(f'AUTO_ARIMA取得完了({com.conv_time_str(run_time)})')

        # モデル情報の保存
        path = f'{save_path}_{currency}_AUTO_ARIMA{('_S' if pdqs else '')}.txt'
        with open(path, 'w') as f:
            f.write(f'実行時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}]{msg}')

        com.dialog(f'AUTO_ARIMA取得が完了、保存しました。\n{com.conv_time_str(run_time)}', 'AUTO_ARIMA取得', )
        subprocess.Popen([cst.TXT_APP_PATH[cst.PC], path])

    finally:
        try: window.close()
        except: pass

    return

def run(currency, df, span, forecast, interval, simu_try, simu_height, str_pdq, str_pdqs, lag, loaded_result=None, ar_only=False):
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
        if 3 == len(pdq):
            pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))
        pdqs = str_pdqs.split(',')
        if 3 == len(pdqs):
            pdqs = (int(pdqs[0]), int(pdqs[1]), int(pdqs[2]))

        # 学習データ作成
        split_len = int(np.ceil(len(eq)))
        train_data = eq[currency][:split_len]

        # テストデータを定義
        test_data = df_seasonal[currency][split_len:]
        train_len = len(train_data)
        test_len = len(test_data)
        total_len = train_len + test_len

        if '-' != interval:
            predict_arima = []

            window = com.progress('ARIMAモデル予測中', ['Predict', int(test_len / interval)], interrupt=True)
            event, values = window.read(timeout=0)

            # トレーニングデータ以降を始点としてテストデータをintervalで指定した数ごとに分けてループする。
            for i in range(train_len, total_len, interval):

                window['Predict'].update(f'{currency} Predict ({str(int((i - train_len) / interval))} / {str(int(test_len / interval))})')
                window['Predict_'].update(int((i - train_len) / interval))

                if 0 == int((i - train_len) / interval) % 10:
                    com.log(f'Predict: {str(int((i - train_len) / interval))} / {str(int(test_len / interval))}')

                model = _create_model(df[:i], 'AR', '', lag, pdqs)
                predictions = model.get_prediction(0, i + interval - 1)
                oos_pred = predictions.predicted_mean.iloc[-interval:]
                predict_arima.extend(oos_pred)
                model.remove_data()

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

        if not ar_only and 3 == len(pdq):
            window = com.progress('ARIMAモデル予測中', ['シミュレーション', simu_try], interrupt=True)
            event, values = window.read(timeout=0)

            # モデルで予測を実行
            if loaded_result is None:
                model = _create_model(train_data, 'SARIMA', pdq, span, pdqs)
            else:
                model = loaded_result

            # 予測データ作成
            forecast_data = pd.DataFrame({'test': test_data})

            simulations = []
            for i in range(simu_try):
                window['シミュレーション'].update(f'{currency} シミュレーション {str(i)} / {str(simu_try)}')
                window['シミュレーション_'].update(i)

                if 0 == i % 100:
                    com.log(f'シミュレーション: {str(i)} / {str(simu_try)}')

                sim = model.simulate(nsimulations=len(test_data), anchor='end')
                simulations.append(sim)

                # 中断イベント
                if _is_interrupt(window, event):
                    return None

            model_summary    = str(model.summary())
            model.remove_data()

            forecast_median = np.median(simulations, axis=0)
            forecast_percentiles = np.percentile(simulations, [simu_height, 100 - simu_height], axis=0)

            forecast_data.loc[:, 'forecast_upper'] = forecast_percentiles[1]
            forecast_data.loc[:, 'forecast_lower'] = forecast_percentiles[0]
            forecast_data.loc[:, 'forecast_median'] = forecast_median

            window.close()

        msg = ', '.join([msg for msg in [
            (f'SARIMA: ({str_pdq.replace(',', ' ')})({str_pdqs.replace(',', ' ')} {str(span)})' if not ar_only and 3 == len(pdq) else ''),
            (f'AR({str(lag)})RMSE: {str(round(predict_rmse, 7))}' if '-' != interval else '')] if '' != msg])

        # チャートの表示定義
        fig1, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=cst.FIG_SIZE, sharex=True)
        fig1.suptitle(currency + '[' + str(len(eq)) + ' - ' + str(forecast) + '] ' + msg.replace('\n', ''), fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(df_seasonal, label='Actual', linewidth=1, color='blue', alpha=0.3)

        if '-' != interval:
            ax1.plot(predict_data['predict'], label='AR', linewidth=1, color='red', alpha=0.5)

        if not ar_only and 3 == len(pdq):
            ax1.fill_between(np.arange(split_len, split_len + len(forecast_data['forecast_median']), 1),
                             forecast_data['forecast_upper'], forecast_data['forecast_lower'], color='orange', alpha=0.2)
            ax1.plot(forecast_data['forecast_median'], label='SARIMA', linewidth=1, color='green', alpha=0.5)

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
        if not ar_only and 3 == len(pdq):
            file_name = f'_ARIMA({str_pdq})({str_pdqs},{span})_AR({str(lag)})'
            file_name += ('Analytics' if loaded_result is None else '_Result')
            save_path = f'{SAVE_PATH}{'Analytics' if loaded_result is None else 'Result'}/{save_path}_{currency}{file_name}'

            with open(f'{save_path}.txt', 'w') as f:
                f.write(f'学習時間: {com.conv_time_str(run_time)} [{df.index[0][:4]} - {df.index[-1][:4]}] '
                        + f'予測期間: {str(forecast)}, ' + (f'予測間隔: {str(interval)}, ' if loaded_result is None else '')
                        + f'シミュレーション: {str(simu_try)}, バンド幅: {str(simu_height)}'
                        + f'\n{msg}\n\n{model_summary}')
            plt.savefig(f'{save_path}.png',  format='png')

            subprocess.Popen([cst.TXT_APP_PATH[cst.PC], f'{save_path}.txt'])
        # 表示の実行
        plt.show()

    finally:
        try: window.close()
        except: pass

def save(currency, df, span, str_pdq, str_pdqs, lag):
    com.log('ARIMAモデル作成開始')

    # モデルの保存
    save_path = f'{SAVE_PATH}Model/{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'

    total_time = 0
    try:
        start_time = com.time_start()

        window = com.progress('', ['ARIMAモデル作成中', 2], interrupt=True)
        event, values = window.read(timeout=0)

        # 基本データからデータ作成
        eq = df.rename(columns={'Close': currency})
        pdq = str_pdq.split(',')
        pdq = (int(pdq[0]), int(pdq[1]), int(pdq[2]))
        pdqs = str_pdqs.split(',')
        pdqs = (int(pdqs[0]), int(pdqs[1]), int(pdqs[2]))

        arima_types = ['AR', 'SARIMA']
        for i in range(len(arima_types)):
            window['ARIMAモデル作成中'].update(f'{currency} {arima_types[i]} モデル作成中')
            window['ARIMAモデル作成中_'].update(i)

            com.log(f'ARIMAモデル作成中: {arima_types[i]} ')
            model = _create_model(eq, arima_types[i], pdq, (lag if 'AR' == arima_types[i] else span), pdqs)
            model_name = (f'AR({str(lag)})' if 'AR' == arima_types[i] else f'SARIMA({str_pdq})({str_pdqs},{span})')
            model.save(f'{save_path}_{currency}_{model_name}.pkl')

            # 中断イベント
            if _is_interrupt(window, event):
                return None

        window.close()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(f'ARIMAモデル作成完了({com.conv_time_str(run_time)})')
        com.dialog(f'ARIMAモデル作成が完了、保存しました。\n{com.conv_time_str(run_time)}', 'ARIMAモデル作成', )

    finally:
        try: window.close()
        except: pass

def _create_model(df, arima_type, pdq, span, pdqs=None):
    try:
        if 'AR' == arima_type:
            model = AutoReg(df, lags=span).fit()
        elif 'SARIMA' == arima_type:
            if pdqs is None:
                model = SARIMAX(df, order=pdq, seasonal_order=(1, 1, 1, span)).fit(disp=False)
            else:
                model = SARIMAX(df, order=pdq, seasonal_order=(pdqs[0], pdqs[1], pdqs[2], span)).fit(disp=False)
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
