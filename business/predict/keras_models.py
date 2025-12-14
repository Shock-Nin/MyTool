#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import numpy as np
import FreeSimpleGUI as sg


from sklearn.metrics import r2_score
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM, GRU, RNN

import japanize_matplotlib
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


def create(currency, model_type, df, train, span, epochs):

    com.log(model_type + 'モデル作成開始')

    fig, ax = plt.subplots(1, 1, figsize=cst.FIG_SIZE, sharex=True)

    total_time = 0
    cnt = 0
    try:
        start_time = com.time_start()

        window = com.progress(model_type + 'モデル作成中', [currency, 1], interrupt=True)
        event, values = window.read(timeout=0)

        # Close(終値)のデータ
        data = df.filter(['Close'])
        dataset = data.values

        # データを0〜1の範囲に正規化
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(dataset)

        # トレーニングデータとして扱う割合
        # training_data_len = int(np.ceil(len(dataset) * .8))
        training_data_len = int(np.ceil(len(dataset) * train))
        # 予測期間
        window_size = int(span)

        train_data = scaled_data[0: int(training_data_len), :]

        # train_dataをx_trainとy_trainに分ける
        x_train, y_train = [], []
        if 'RNN' == model_type:
            for i in range(window_size * 2, len(train_data)):
                x_train.append(train_data[i - window_size: i, 0])
                y_train.append(train_data[i, 0])
        else:
            for i in range(window_size, len(train_data)):
                x_train.append(train_data[i - window_size: i, 0])
                y_train.append(train_data[i, 0])

        # numpy arrayに変換
        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

        units = 50
        dropout = 0.2

        model = Sequential()
        if 'LSTM' == model_type:
            model.add(LSTM(units=units, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            model.add(Dropout(dropout))
            model.add(LSTM(units=units, return_sequences=True))
            model.add(Dropout(dropout))
            model.add(LSTM(units=units, return_sequences=True))
            model.add(Dropout(dropout))
            model.add(LSTM(units=units))
            model.add(Dropout(dropout))

        elif 'GRU' == model_type:
            model.add(GRU(units=units, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            model.add(Dropout(dropout))
            model.add(GRU(units=units, return_sequences=True))
            model.add(Dropout(dropout))
            model.add(GRU(units=units, return_sequences=True))
            model.add(Dropout(dropout))
            model.add(GRU(units=units))
            model.add(Dropout(dropout))

        elif 'RNN' == model_type:
            model.add(RNN(units=units, return_sequences=True, input_shape=(x_train.shape[1], 1)))
            model.add(Dropout(dropout))
            model.add(RNN(units=units, return_sequences=True))
            model.add(Dropout(dropout))
            model.add(RNN(units=units, return_sequences=True))
            model.add(Dropout(dropout))
            model.add(RNN(units=units))
            model.add(Dropout(dropout))

        model.add(Dense(units=1))
        model.compile(optimizer='adam', loss='mean_squared_error')
        history = model.fit(x_train, y_train, batch_size=32, epochs=epochs)

        model.summary()

        # テストデータを作成
        test_data = scaled_data[training_data_len - window_size:, :]

        x_test = []
        y_test = dataset[training_data_len:, :]
        for i in range(window_size, len(test_data)):
            x_test.append(test_data[i - window_size:i, 0])

        # numpy arrayに変換
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

        # 予測を実行する
        predictions = model.predict(x_test)
        predictions = scaler.inverse_transform(predictions)

        train = data[:training_data_len]
        valid = data[training_data_len:]
        valid['Predictions'] = predictions

        # 二乗平均平方根誤差(RMSE): 0に近いほど良い、決定係数(r2): 1に近いほど良い
        fig.suptitle(model_type + ' | ' + currency + ': 二乗平均平方根誤差(RMSE ↓0) '
                     + str(round(np.sqrt(np.mean(((predictions - y_test) ** 2))), 5))
                     + '| 決定係数(r2 ↑1) ' + str(round(r2_score(y_test, predictions), 5)), fontsize=cst.FIG_FONT_SIZE)

        plt.plot(train['Close'], linewidth=2)
        plt.plot(valid[['Close', 'Predictions']], linewidth=1)

        plt.gcf().autofmt_xdate()
        plt.xticks(np.arange(0, len(df), step=(len(df) / 10)))
        plt.legend(['Train', 'Val', 'Predictions'], ncol=3, loc='upper left')
        plt.grid()

        run_time = com.time_end(start_time)
        total_time += run_time
        com.log(model_type + '[' + currency + ']予測完了(' + com.conv_time_str(run_time) + ') ')

        window.close()
        plt.show()
    finally:
        try: window.close()
        except: pass

    com.log(model_type + 'モデル作成完了(' + com.conv_time_str(total_time) + ')')

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
