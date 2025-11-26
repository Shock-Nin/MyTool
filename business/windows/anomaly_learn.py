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


import statsmodels.datasets.co2 as co2

from typing import Tuple
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pydataset import data

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
        # co2_raw = co2.load().data
        # # df = co2_raw.iloc[353:]  # 1965以降のデータを抽出
        # # df = df.resample('M').mean()  # 月次データに変換 (月の最終日を取得)"
        # df.index.name = "YEAR"
        #
        # print(co2_raw)
        # print(df)
        # # STL分解
        # stl = sm.tsa.STL(df['usdjpy']).fit()
        #
        # # それぞれの成分を描画
        # fig, ax = plt.subplots(4, 1, figsize=(5, 4), sharex=True)
        #
        # df['usdjpy'].plot(ax=ax[0], c='black')
        # ax[0].set_title('Original Data')
        #
        # stl.trend.plot(ax=ax[1], c='black')
        # ax[1].set_title('Trend')
        #
        # stl.seasonal.plot(ax=ax[2], c='black')
        # ax[2].set_title('Seasonal')
        #
        # stl.resid.plot(ax=ax[3], c='black')
        # ax[3].set_title('Residual')
        #
        # plt.tight_layout()
        # plt.show()

        # x = df['Time']
        # y = df['usdjpy']
        # x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        #
        # np.random.seed(0)
        # x = np.random.rand(100, 1) * 5  # 独立変数（例：家の大きさ）
        # y = 3 * x + np.random.randn(100, 1) * 2  # 従属変数（例：家の価格）
        # x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        #
        # model = LinearRegression()
        # model.fit(x_train, y_train)
        # # テストデータで予測
        # predictions = model.predict(x_test)
        #
        # # 予測結果をプロット
        # plt.scatter(x_test, y_test, color='black', label ='Actual data')
        # plt.plot(x_test, predictions, color='blue', linewidth = 3, label ='Linear regression line')
        # plt.xlabel('x value')
        # plt.ylabel('y value')
        # plt.title('Linear Regression Example')
        # plt.legend()
        # plt.show()




        # for key in df:
        #     if '' == key:
        #         continue
        #     # 製品別の合計データセット作成
        #     querystr = 'Time == "' + key + '"'
        #     df_target = df.query(querystr)
        #     df_target = df_target.sort_values(by='Time', ascending=True)
        #     df_target = df_target.groupby('Time').sum().reset_index()
        #     days = list(df_target['Time'].drop_duplicates())
        #
        #     # 階差
        #     df_target['eurusd'] = df_target['gbpusd'].diff()
        #
        #     # 製品の日の受注推移と階差の描画
        #     fig, ax = plt.subplots()
        #     ax.plot(days, df_target['gbpusd'],
        #             color="blue", label='ori_data')
        #     ax.plot(days, df_target['eurusd'],
        #             color="red", label='Diff')
        #     # ラベル
        #     ax.set_ylabel('y')
        #     ax.set_xlabel('x')
        #     # 系列
        #     plt.legend(loc='upper right')
        #
        #     plt.show()


        # df_target = df[['Time', 'usdjpy']]
        # # df_target = df_target.query('Time <= \'2016/12/31\'')
        # # 日付項目インデックス化
        # df_target = df_target.set_index('Time')
        #
        # # SARIMAモデルによる予測
        # SARIMA_target = sm.tsa.statespace.SARIMAX(df_target, order=(3, 1, 2), seasonal_order=(1, 1, 1, 7)).fit()
        # pred = SARIMA_target.predict('2015/01/05 00:00:00', '2017/12/29 00:00:00')
        #
        # # テストデータdf_test
        # df_test = df[['Time', 'usdjpy']]
        # df_test = df_test.query('(\'2015/01/01\' <= Time <= \'2017/12/31\')')
        # df_test = df_test[['Time', 'usdjpy']]
        #
        # # グラフの描画
        # fig, ax = plt.subplots()
        # ax.plot(pred.index, df_test['usdjpy'], color='b', label='actual')
        # ax.plot(pred, color='r', label='pred')
        # ax.legend()
        # ax.set_ylabel('cur')
        # ax.set_xlabel('Time')
        # plt.show()

        # except Exception as e:
        #     com.dialog('エラーが発生しました。\n' + str(e), 'モデル作成エラー発生', lv='W')
        #     return
        #

        # # 訓練データと検証データ
        # train = df.query('(\'2020/01/01\' <= ds <= \'2021/12/31\')')
        # valid = df.query('(\'2022/01/01\' <= ds <= \'2022/12/31\')')
        #
        # study = optuna_parameter(train, valid)
        #
        # # NeuralProphetによる予測
        # m = NeuralProphet(
        #     changepoints_range=study.best_params['changepoints_range'],
        #     n_changepoints=study.best_params['n_changepoints'],
        #     trend_reg=study.best_params['trend_reg'],
        #     yearly_seasonality=True,
        #     weekly_seasonality=True,
        #     daily_seasonality=False,
        #     seasonality_reg=study.best_params['seasonality_reg'],
        #     epochs=None,
        #     batch_size=None,
        #     seasonality_mode=study.best_params['seasonality_mode'])
        #
        #
        # # モデル適用
        # metric = m.fit(train, freq='D')
        # future = m.make_future_dataframe(train, periods=365)
        # forecast = m.predict(future)
        # pred = forecast[['ds', 'yhat1']]
        #
        # # グラフの描画
        # fig, ax = plt.subplots()
        # ax.plot(pred['ds'], valid['y'], color='b', label='actual')
        # ax.plot(pred['ds'], pred['yhat1'], color='r', label='pred')
        # ax.legend()
        # ax.set_ylabel('quantity')
        # ax.set_xlabel('Date')
        # plt.show()

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