#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess

from common import com
from const import cst

import numpy as np
import FreeSimpleGUI as sg


from sklearn.metrics import r2_score
from sklearn.preprocessing import MinMaxScaler
# from tensorflow import keras
# from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import LSTM, GRU, SimpleRNN

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


SAVE_PATH = f'{cst.MODEL_PATH[cst.PC]}models/'


def run(model_type, currency, df, forecast, interval, count, middle, dropout, epochs, loaded_result=None):
    com.log(model_type + 'モデル予測開始')

    # 保存パス
    save_time = f'{com.str_time()[:16].replace('-', '').replace(':', '').replace(' ', '_')}'
    save_path = f'{SAVE_PATH}{model_type}/{'Analytics' if loaded_result is None else 'Result'}/{save_time}_{currency}'
    model_path = f'{SAVE_PATH}{model_type}/Model/{save_time}_{currency}'

    total_time = 0
    try:
        start_time = com.time_start()

        window = com.progress( '', [currency, 2], interrupt=True)
        event, values = window.read(timeout=0)

        window[currency].update(f'{currency} {model_type}モデル推論中: {epochs}エポック')
        window[currency + '_'].update(0)

        # データ作成
        df = df.rename(columns={'Close': currency})
        dataset = df.filter([currency]).values

        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(dataset)

        split_len = int(np.ceil(len(dataset) - forecast))
        valid = df[split_len:]

        # 学習データをx_trainとy_trainに分け、numpy arrayに変換
        train_data = scaled_data[0: split_len, :]
        x_train, y_train = [], []
        for i in range(interval, len(train_data)):
            x_train.append(train_data[i - interval: i, 0])
            y_train.append(train_data[i, 0])
        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

        # テストデータをx_testとy_testに分け、numpy arrayに変換
        test_data = scaled_data[split_len - count:, :]
        x_test = []
        y_test = scaled_data[split_len:, :]
        # y_test = dataset[split_len:, :]
        for i in range(count, len(test_data)):
            x_test.append(test_data[i - count: i, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

        # shape = (None, )
        # shape = (count, 1)
        # df = df[currency]
        # for term in range(1, 2):
        #     n, date, x, y, l_x, l_y = _get_x_y_lx_ly(currency, df[currency], interval, count, term)
        #     model = _create_model(model_type, middle, dropout, shape)
        #     # history = model.fit(l_x, l_y, epochs=epochs, batch_size=32, verbose=0)
        #     history = model.fit(x_train, y_train, epochs=epochs, batch_size=32, validation_split=0.25, verbose=0)
        #     # history = model.fit(l_x, l_y, epochs=epochs, batch_size=32, validation_split=0.25, verbose=0)

        # 呼び出しモデルがなければ、作成して学習して保存
        if loaded_result is None:
            shape = (np.array(x_train).shape[1], 1)
            model = _create_model(model_type, middle, dropout, shape)

            # 学習の実行
            history = model.fit(x_train, y_train, epochs=epochs, batch_size=32, validation_split=0.25)
            loss = history.history['loss']
            val_loss = history.history['val_loss']

            # モデルの保存
            model.save(f'{model_path}_{model_type}.keras')

        # 呼び出しモデルがあれば、そのまま利用
        else:
            model = loaded_result

        # 予測の実行
        predictions = model.predict(x_test)
        predictions = scaler.inverse_transform(predictions)
        valid['Predictions'] = predictions

        window.close()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(model_type + '[' + currency + ']予測完了(' + com.conv_time_str(run_time) + ') ')

        # Lossチャートの表示定義(非表示・保存専用)
        str_title = f'{currency}[{str(epochs)}] {df.index[0][:4]} - {df.index[-1][:4]}: {model_type}'

        msg = f'予測期間: {str(forecast)}, 予測間隔: {str(interval)}, 予測数: {str(count)}, ' \
              + f'中間層: {str(middle)}, ドロップ: {'-' if dropout < 0 else str(dropout)}' \
              + f'\n学習時間: {com.conv_time_str(run_time)}, ' \
              + f'RMSE: {str(round(np.sqrt(np.mean(((predictions - y_test) ** 2))), 7))}, ' \
              + f'r2: {str(round(r2_score(y_test, predictions), 7))}'

        # 呼び出しモデルがない場合は、Lossチャートを作成
        if loaded_result is None:
            str_loss = f'Loss Curve({str(round(loss[-1], 7))}, {str(round(val_loss[-1], 7))})'
            msg += f' | {str_loss}'

            fig2, (ax2) = plt.subplots(1, 1, figsize=(int (cst.FIG_SIZE[0] * 0.5), int(cst.FIG_SIZE[1] * 0.8)), sharex=True)
            fig2.suptitle(f'{str_title} | {msg}', fontsize=int(cst.FIG_FONT_SIZE * 0.7))
            ax2.plot(np.arange(len(loss)), loss, label='loss', linewidth=1)
            ax2.plot(np.arange(len(val_loss)), val_loss, label='val_loss', linewidth=1)

            plt.tight_layout()
            plt.xticks(np.arange(0, epochs, step=(epochs / 10)))
            ax2.legend(ncol=2, loc='upper right')
            plt.grid()
            plt.grid()

            # Lossチャートの保存、ここでは開かない
            loss_png_name = f'{save_path}_Loss_Analytics.png'
            plt.savefig(loss_png_name, format='png')
            plt.close()

        # 予測チャートの表示定義
        fig1, (ax1) = plt.subplots(1, 1, figsize=cst.FIG_SIZE, sharex=True)
        fig1.suptitle(f'{str_title} | {msg}', fontsize=cst.FIG_FONT_SIZE)

        ax1.plot(df[currency], label='Actual', linewidth=1, color='blue', alpha=0.3)
        ax1.plot(valid['Predictions'], label='Predict', linewidth=1, color='red', alpha=0.5)

        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.xticks(np.arange(0, len(df), step=(len(df) / 10)))
        ax1.legend(ncol=2, loc='upper left')
        plt.grid()
        plt.grid()

        # 予測チャートの保存
        file_name = ('_Analytics' if loaded_result is None else '_Result')
        plt.savefig(f'{save_path}{file_name}.png', format='png')

        # 呼び出しモデルがない場合は、Lossチャートを表示
        if loaded_result is None:
            subprocess.Popen([cst.IMG_APP_PATH[cst.PC], loss_png_name], shell='Win' == cst.PC)
            com.sleep(2)
            os.remove(loss_png_name)

        # 予測チャートの表示
        plt.show()
    finally:
        try: window.close()
        except: pass

# def _get_x_y_lx_ly(currency, df, interval, count, term):
#
#     date = np.array(df.index[interval * term: interval * (1 + term)])
#     x = np.array(df.index.values[interval * term: interval * (1 + term)])
#     y = np.array(df[interval * term: interval * (1 + term)])
#
#     n = len(y) - count
#     l_x = np.zeros((n, count))
#     l_y = np.zeros((n, count))
#
#     for i in range(0, n):
#         l_x[i] = y[i: i + count]
#         l_y[i] = y[i + 1: i + count + 1]
#
#     l_x = l_x.reshape(n, count, 1)
#     l_y = l_y.reshape(n, count, 1)
#
#     return n, date, x, y, l_x, l_y

# モデル作成
def _create_model(model_type, middle, dropout, shape):

    layer = (LSTM if 'LSTM' == model_type else GRU if 'GRU' == model_type else SimpleRNN)

    model = Sequential()
    model.add(layer(middle, return_sequences=True, input_shape=shape))
    if 0 <= dropout: model.add(Dropout(dropout))
    model.add(layer(middle, return_sequences=True))
    if 0 <= dropout: model.add(Dropout(dropout))
    model.add(layer(middle, return_sequences=True))
    if 0 <= dropout: model.add(Dropout(dropout))
    model.add(layer(middle))

    model.add(Dense(units=1, activation='linear'))
    model.compile(optimizer='adam', loss='mean_squared_error')

    return model

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
