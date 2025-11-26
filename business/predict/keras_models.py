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

import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


def create(model_type, dict_df, inputs):

    com.log(model_type + 'モデル作成開始')

    fig, ax = plt.subplots(1, len(dict_df), figsize=(16, 6))
    fig.suptitle(model_type + ' [' + ', '.join(currency.replace('USD', '') for currency in dict_df) + ']')

    total_time = 0
    cnt = 0
    try:
        for currency in dict_df:
            start_time = com.time_start()

            window = com.progress(model_type + 'モデル作成中', [currency, len(dict_df)], interrupt=True)
            event, values = window.read(timeout=0)

            window[currency].update(currency + ' (' + str(cnt) + ' / ' + str(len(dict_df)) + ')')
            window[currency + '_'].update(cnt)

            df = dict_df[currency]

            # Close(終値)のデータ
            data = df.filter(['Close'])
            dataset = data.values

            # データを0〜1の範囲に正規化
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(dataset)

            # 全体の80%をトレーニングデータとして扱う
            training_data_len = int(np.ceil(len(dataset) * .8))
            # どれくらいの期間をもとに予測するか
            window_size = int(inputs[0])

            train_data = scaled_data[0:int(training_data_len), :]

            # train_dataをx_trainとy_trainに分ける
            x_train, y_train = [], []
            for i in range(window_size, len(train_data)):
                x_train.append(train_data[i - window_size:i, 0])
                y_train.append(train_data[i, 0])

            # numpy arrayに変換
            x_train, y_train = np.array(x_train), np.array(y_train)
            x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

            model = Sequential()
            if 'LSTM' == model_type:
                model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
                model.add(Dropout(0.2))
                model.add(LSTM(units=50, return_sequences=True))
                model.add(Dropout(0.2))
                model.add(LSTM(units=50, return_sequences=True))
                model.add(Dropout(0.2))
                model.add(LSTM(units=50))
                model.add(Dropout(0.2))

            elif 'GRU' == model_type:
                model.add(GRU(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
                model.add(Dropout(0.2))
                model.add(GRU(units=50, return_sequences=True))
                model.add(Dropout(0.2))
                model.add(GRU(units=50, return_sequences=True))
                model.add(Dropout(0.2))
                model.add(GRU(units=50))
                model.add(Dropout(0.2))

            elif 'RNN' == model_type:
                model.add(RNN(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
                model.add(Dropout(0.2))
                model.add(RNN(units=50, return_sequences=True))
                model.add(Dropout(0.2))
                model.add(RNN(units=50, return_sequences=True))
                model.add(Dropout(0.2))
                model.add(RNN(units=50))
                model.add(Dropout(0.2))

            model.add(Dense(units=1))
            model.compile(optimizer='adam', loss='mean_squared_error')
            history = model.fit(x_train, y_train, batch_size=32, epochs=int(inputs[1]))

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
            # try:
            #     predictions = scaler.inverse_transform(predictions)
            # except:
            #     com.log('Predictionsエラー')

            # 二乗平均平方根誤差（RMSE）: 0に近いほど良い
            rmse = np.sqrt(np.mean(((predictions - y_test) ** 2)))

            # 決定係数(r2) : 1に近いほど良い
            r2s = r2_score(y_test, predictions)

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log(model_type + ' [' + currency + ']予測完了(' + com.conv_time_str(run_time) + ') '
                    + ' 二乗平均平方根誤差(RMSE) ↓ 0：'+ str(rmse) + ' | 決定係数(r2) ↑ 1：'+ str(r2s))

            train = data[:training_data_len]
            valid = data[training_data_len:]
            try:
                valid['Predictions'] = predictions
            except:
                com.log('Predictionsエラー(valid)')

            ax[cnt].plot(train['Close'], linewidth=2)
            ax[cnt].plot(valid[['Close', 'Predictions']], linewidth=1)

            cnt += 1
            window.close()

        plt.gcf().autofmt_xdate()
        plt.legend(['Train', 'Val', 'Predictions'], loc='lower center')
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
