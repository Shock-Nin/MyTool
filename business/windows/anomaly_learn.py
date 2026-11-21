#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from common import my_sql
from const import cst

import json
import glob
import datetime
import pandas as pd
import FreeSimpleGUI as sg

import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
import optuna
import tensorflow as tf
import tensorflow.keras as keras

from neuralprophet import NeuralProphet
from sklearn.metrics import mean_absolute_error
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

DAYWEEKS = ['Week', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']

MODEL_SKIP_DAYS = ['1225', '0101']

class AnomalyLearn:

    def __init__(self, function):
        self.function = function

    def do(self):
        getattr(self, '_' + self.function)()

    def _create_model(self):
        inputs = com.input_box('モデル作成 開始しますか？', '開始確認', [
            ['開始年', int(com.str_time()[:4]) - 10],
            ['終了年', int(com.str_time()[:4]) - 1],
            # ['1=H, 2=D, 3=M, 4=W', '1'], ['1=ボラ, 2=騰落, 3=推移', '1']])
            ['1=H, 2=D, 3=M, 4=W', '2'], ['1=ボラ, 2=騰落, 3=推移', '1']])
        if inputs[0] <= 0:
            return
        try:
            files = glob.glob(cst.HST_PATH[cst.PC].replace('\\', '/') + '_stat/????'
                              + {'1': 'H', '2': 'D', '3': 'M', '4': 'W'}[inputs[1][2]] + '.csv')
            files = sorted(files)

            try:
                years = [year for year in range(int(inputs[1][0]), int(inputs[1][1]) + 1)]
                cnt = 0
                while cnt < len(files):
                    if int(files[cnt].split('/')[-1].replace('.csv', '')) in years:
                        cnt += 1
                    else:
                        del files[cnt]
            except:
                pass

            df = pd.read_csv(files[0])
            if 1 < len(files):
                for i in range(1, len(files)):
                    df = pd.concat([df, pd.read_csv(files[i])])

            df = df.drop([key for key in df if not
            ('Time' == key or (-1 if '3' == inputs[1][3] else 0) <= key.find('_Vola' if '1' == inputs[1][3] else '_UpDn'))], axis=1)
            [df.rename(columns={key: key.replace('USD', '').replace('X_', '').replace('Z_', '').split('_')[0]}, inplace=True) for key in df ]

        except Exception as e:
            com.dialog('エラーが発生しました。\n' + str(e), 'データ取得エラー発生', lv='W')
            return

        title = ('Vola' if '1' == inputs[1][3] else 'Up Down' if '2' == inputs[1][3] else 'Price')
        title += ' (' + ('Hour' if '1' == inputs[1][2] else 'Day' if '2' == inputs[1][2] else
                 'Month' if '3' == inputs[1][2] else 'Week') + ')'
        # try:
        # pd.to_datetime(df['Time'])

        # df.astype({'usdjpy': np.float64})
        df.set_index('Time', inplace=True)

        # df.rename(columns={'Time': 'ds'}, inplace=True)

        df.fillna(0, inplace=True)
        [df.astype({key: np.asarray(dt for dt in df[key])}) for key in df if 'Time' != key]



        # df=data('AirPassengers')


        # print(df)
        #
        # # データのロードとプロット
        df = load_and_plot_data(df, title)

        # ARIMAモデルの適用
        apply_arima_model(df, title, order=(2, 1, 2))

        # SARIMAモデルの適用 (ここでいうseasonal_orderは(季節性成分のAR次数, 季節性成分の階差, 季節性成分のMA次数, 季節周期)を指します)
        apply_sarima_model(df, title, order=(1, 1, 1), seasonal_order=(1, 1, 0, 12))










        #
        com.dialog('モデル作成完了しました。', 'モデル作成完了',)
        return ''


# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False


def objective_variable(train, valid):
    # パラメータ設定
    def objective(trial):
        params = {
            'changepoints_range': trial.suggest_discrete_uniform('changepoints_range', 0.8, 0.95, 0.01),
            'n_changepoints': trial.suggest_int('n_changepoints', 50, 65),
            'trend_reg': trial.suggest_discrete_uniform('trend_reg', 0, 2, 0.01),
            'seasonality_reg': trial.suggest_discrete_uniform('seasonality_reg', 0, 1, 0.2),
            'seasonality_mode': trial.suggest_categorical('seasonality_mode', ['additive', 'multiplicative'])
        }
        # パラメータ適用によるモデル
        m = NeuralProphet(
            changepoints_range=params['changepoints_range'],
            n_changepoints=params['n_changepoints'],
            trend_reg=params['trend_reg'],
        yearly_seasonality = True,
        weekly_seasonality = True,
        daily_seasonality = False,
        seasonality_reg = params['seasonality_reg'],
        epochs = None,
        batch_size = None,
        seasonality_mode = params['seasonality_mode'])

        # モデル予測
        future = m.make_future_dataframe(train, periods=len(valid))
        forcast = m.predict(future)

        # MAE
        train_y = train['usdjpy'][-len(valid):]
        forcast_y = forcast['yhat1']
        MAE = mean_absolute_error(train_y, forcast_y)

        return MAE

    return objective


# パラメータの最適値探索
def optuna_parameter(train, valid):
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=42))
    study.optimize(objective_variable(train, valid), timeout=2400)
    optuna_best_params = study.best_params

    return optuna_best_params


def load_and_plot_data(df, title):
# def load_and_plot_data(df) -> pd.DataFrame:
    """データをロードし、プロットする関数"""
    df.plot()  # データのプロット
    plt.title(title)
    plt.show()
    return df


def apply_arima_model(df, title, order):
# def apply_arima_model(df: pd.DataFrame, order: Tuple[int]) -> None:
    """ARIMAモデルを適用する関数"""

    # df.plot()  # データのプロット
    model = ARIMA(df, order=order)  # モデルの設定
    model_fit = model.fit()  # モデルの学習

    # モデルの結果のサマリーを表示
    print(model_fit.summary())
    # プロット
    model_fit.plot_predict(dynamic=False)
    plt.title('ARIMA ' + title)
    plt.show()


def apply_sarima_model(df, title, order, seasonal_order):
# def apply_sarima_model(df: pd.DataFrame, order: Tuple[int], seasonal_order: Tuple[int]) -> None:
    """SARIMAモデルを適用する関数"""
    # df.plot()  # データのプロット
    model = SARIMAX(df, order=order, seasonal_order=seasonal_order)  # モデルの設定
    model_fit = model.fit()  # モデルの学習

    # モデルの結果のサマリーを表示
    print(model_fit.summary())
    # プロット
    model_fit.plot_diagnostics(figsize=(16, 8))
    plt.title('SARIMA ' + title)
    plt.show()