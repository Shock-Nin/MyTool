#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common import com
from const import cst

import numpy as np
import statistics
import pandas as pd
import FreeSimpleGUI as sg


from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

from keras.models import Sequential
from keras.layers import Dense, GRU
from keras.optimizers import RMSprop


import pandas_datareader as pdr

import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')


def gru(dict_df, inputs):

    fig, ax = plt.subplots(3, len(dict_df), figsize=(16, 8))
    fig.suptitle(', '.join(currency.replace('USD', '') for currency in dict_df))

    total_time = 0
    cnt = 0
    try:
        for currency in dict_df:
            start_time = com.time_start()

            title = currency + ' 損失値・実終値と予測・未来予測'

            window = com.progress('GRUモデル作成中', [title, len(dict_df)], interrupt=True)
            event, values = window.read(timeout=0)

            window[title].update(currency + ' (' + str(cnt) + ' / ' + str(len(dict_df)) + ')')
            window[title + '_'].update(cnt)

            df = dict_df[currency]

            closing_price = df[['Close']].values

            ## 訓練・検証・テスト用データ
            (X_train, y_train) = _data_split(closing_price, int(inputs[0]), -100, int(inputs[0]))
            (X_valid, y_valid) = _data_split(closing_price, -100, -50, int(inputs[0]))
            (X_test, y_test) = _data_split(closing_price, -50, 0, int(inputs[0]))

            ## 標準化:scalerは正規化するための関数
            ## X のみ次元を変換（2次元 ⇒ 3次元）
            scaler = StandardScaler()
            scaler.fit(X_train)
            X_train_std = scaler.transform(X_train).reshape(-1, int(inputs[0]), 1)
            X_valid_std = scaler.transform(X_valid).reshape(-1, int(inputs[0]), 1)
            X_test_std = scaler.transform(X_test).reshape(-1, int(inputs[0]), 1)

            scaler.fit(y_train)
            y_train_std = scaler.transform(y_train)
            y_valid_std = scaler.transform(y_valid)

            # X_train_std.shape[-1] 行列X_train_stdの列数
            length_of_sequence = X_train_std.shape[-1]
            # 隠れ層の数
            n_hidden = 256

            ## 訓練 RNN(ここでmodelを作る)
            model = Sequential()
            model.add(GRU(n_hidden,
                          dropout=0.2,
                          recurrent_dropout=0.2,
                          return_sequences=False,
                          input_shape=(None, X_train_std.shape[-1])))
            model.add(Dense(1))  ##ニューロン数

            model.compile(optimizer=RMSprop(), loss='mae', metrics=['accuracy'])

            result = model.fit(X_train_std, y_train_std,
                               verbose=0,  ## 詳細表示モード
                               epochs=int(inputs[1]),
                               batch_size=64,
                               shuffle=True,
                               validation_data=(X_valid_std, y_valid_std))

            ## 訓練の損失値をプロット
            epochs = range(len(result.history['loss']))

            ax[0, cnt].plot(epochs, result.history['loss'], 'bo', alpha=0.6, marker='.', label='Train', linewidth=1)
            ax[0, cnt].plot(epochs, result.history['val_loss'], 'r', alpha=0.6, label='Valid', linewidth=1)
            # ax[cnt].xlabel('Epoch')
            # ax[cnt].ylabel('Loss')

            ## 予測値
            df_predict_std = pd.DataFrame(model.predict(X_test_std), columns=['Predict'])

            ## TODO 予測値を元に戻す(正規化の解除)
            # predict = scaler.inverse_transform(df_predict_std['Predict'].values)
            predict = df_predict_std['Predict'].values

            ## 予測結果をプロット
            pre_date = df.index[-len(y_test):].values

            ax[1, cnt].plot(pre_date, y_test, 'b', alpha=0.6, marker='.', label='Real', linewidth=1)
            ax[1, cnt].plot(pre_date, predict, 'r', alpha=0.6, marker='.', label='Predict', linewidth=1)

            # 未来の株価予想
            future_test = X_test_std[-1].T
            # 1つの学習データの時間の長さ
            time_length = future_test.shape[1]
            # 未来の予測データを保存していく変数
            future_result = np.empty((1))

            # 10日間の日経平均の予測をする
            for step2 in range(10):
                # future_testを3次元に変換
                test_data = np.reshape(future_test, (1, time_length, 1))
                # 予測値をbatch_predict_stdに格納
                batch_predict_std = model.predict(test_data)
                # batch_predict_stdの正規化を解除する（step2日目の予測）
                batch_predict = scaler.inverse_transform(batch_predict_std)
                # 最初の要素を消す
                future_test = np.delete(future_test, 0)
                # future_testの最後尾にbatch_predict_stdを追加する
                future_test = np.append(future_test, batch_predict_std)
                # future_resultにstep2日目のデータを追加
                future_result = np.append(future_result, batch_predict)

            # 未来の予測データを保存していく変数作成時に出来た不要な最初の要素を削除
            future_result = np.delete(future_result, 0)

            # 予測結果をプロット
            pre_date = df.index[-len(y_test + future_result):].values

            ax[2, cnt].plot(pre_date, y_test, 'b', alpha=0.6, marker='.', label='Real', linewidth=1)
            ax[2, cnt].plot(pre_date, predict, 'r', alpha=0.6, marker='.', label='Predict', linewidth=1)
            ax[2, cnt].plot(range(len(predict), len(future_result) + len(predict)), future_result, 'g', alpha=0.6, marker='.',
                     label='Future', linewidth=1)

            run_time = com.time_end(start_time)
            total_time += run_time
            com.log(currency + '予測完了(' + com.conv_time_str(run_time) + ') '
                    + ' 二乗平均平方根誤差(RMSE) → 0：'+ str(np.sqrt(mean_squared_error(y_test, predict))))

            cnt += 1
            window.close()

        plt.gcf().autofmt_xdate()
        ax.legend()
        # plt.legend(['Train', 'Valid', 'Real', 'Predict', 'Real', 'Predict', 'Future'], loc='lower center')
        # fig.legend()
        plt.show()
    finally:
        try: window.close()
        except: pass

    com.log('GRUモデル作成完了(' + com.conv_time_str(total_time) + ')')


## 訓練・検証・テスト用データを作成
## 過去50日分の株価より当日の株価とする
def _data_split(data, start, end, lookback):
    length = abs(start - end)

    X = np.zeros((length, lookback))
    y = np.zeros((length, 1))

    for i in range(length):
        j = start - lookback + i
        k = j + lookback

        X[i] = data[j:k, 0]
        y[i] = data[k, 0]

    return X, y

# 中断イベント
def _is_interrupt(window, event):
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
