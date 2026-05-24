#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MT5ティックデータから1時間足・日足データを作成するモジュール

処理内容:
1. MT5tickフォルダ内の期間別フォルダからティックデータを読み込み
2. 1時間足の4本値(OHLC)を作成（土日除外）
3. Baseフォルダに1時間足OHLCを出力
4. H1フォルダに1時間足終値を出力
5. D1フォルダに日足終値を出力
"""
from common import com
from const import cst

import os
import glob
import pandas as pd
import FreeSimpleGUI as sg


# ベースパス
BASE_PATH = cst.CURRENT_PATH + '/OneDrive/ドキュメント/Data/History'
CSV_PATH = BASE_PATH + '/MT5tick'
OUT_BASE_PATH = BASE_PATH + '/Base'
OUT_H1_PATH = BASE_PATH + '/H1'
OUT_D1_PATH = BASE_PATH + '/D1'

# 対象通貨リスト
TARGET_CURRENCIES = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD', 'USDCHF',
                     'USDHKD', 'USDSEK', 'USDPLN', 'USDNOK', 'USDTRY', 'USDZAR', 'USDMXN']


class TickToOhlc:

    def __init__(self, event):
        self.event = event
        self.is_interrupt = False
        self.total_time = 0

    def do(self):
        """メイン処理"""
        if self.event == 'create_all':
            self.create_all()
        elif self.event == 'create_base':
            self.create_base()
        elif self.event == 'create_h1_d1':
            self.create_h1_d1()
        return True

    def create_all(self):
        """全処理を実行"""
        if com.question('ティックデータから全データを作成しますか？\n(Base, H1, D1)', '開始確認') <= 0:
            return

        self.create_base()
        if not self.is_interrupt:
            self.create_h1_d1()

    def create_base(self):
        """ティックデータから1時間足4本値を作成してBaseに出力"""
        if com.question('ティックデータからBase(1時間足OHLC)を作成しますか？', '開始確認') <= 0:
            return

        start_time = com.time_start()

        # 期間フォルダ一覧を取得
        period_folders = sorted(glob.glob(CSV_PATH + '/*_*'))
        if 0 == len(period_folders):
            com.dialog(CSV_PATH + ' にフォルダが存在しません。', title='フォルダ不在', lv='w')
            return

        # 全CSVファイルを通貨ペアごとに収集
        currency_files = {}
        for folder in period_folders:
            csv_files = glob.glob(folder + '/*.csv')
            for csv_file in csv_files:
                pair = os.path.basename(csv_file).replace('.csv', '')
                if pair not in currency_files:
                    currency_files[pair] = []
                currency_files[pair].append(csv_file)

        com.log('処理対象: ' + str(len(currency_files)) + ' 通貨ペア')

        # 進捗表示
        window = com.progress('Base(1時間足OHLC)作成中',
                              ['通貨ペア', len(currency_files)], interrupt=True)
        event, values = window.read(timeout=0)

        try:
            for i, (pair, files) in enumerate(sorted(currency_files.items())):
                if self.is_interrupt:
                    break

                window['通貨ペア'].update(pair + ' (' + str(i + 1) + ' / ' + str(len(currency_files)) + ')')
                window['通貨ペア_'].update(i + 1)

                # ティックデータを読み込んで1時間足に変換
                df_h1 = self._convert_tick_to_h1(pair, files, window)

                if df_h1 is not None and len(df_h1) > 0:
                    # 出力先を決定
                    out_path = self._get_output_path(pair, OUT_BASE_PATH)
                    df_h1.to_csv(out_path, index=False)
                    com.log('Base出力: ' + out_path + ' (' + str(len(df_h1)) + '行)')

                # 中断イベント
                event, values = window.read(timeout=0)
                if _is_interrupt(window, event):
                    self.is_interrupt = True
                    break

        finally:
            try:
                window.close()
            except:
                pass

        run_time = com.time_end(start_time)
        self.total_time += run_time
        com.log('Base作成' + ('中断' if self.is_interrupt else '完了') +
                '(' + com.conv_time_str(run_time) + ')')
        com.dialog('Base作成' + ('中断' if self.is_interrupt else '完了') +
                   'しました。(' + com.conv_time_str(run_time) + ')', 'Base作成')

    def _convert_tick_to_h1(self, pair, files, window):
        """ティックデータを1時間足に変換"""
        all_data = []

        for file in sorted(files):
            com.log('読み込み中: ' + file)

            try:
                # チャンク読み取りで大きなファイルを処理
                # CSVフォーマット: Date,Time,Bid,Ask,Last(?),Volume
                chunks = pd.read_csv(file, header=None, chunksize=1000000,
                                     names=['Date', 'Time', 'Bid', 'Ask', 'Last', 'Volume'])

                for chunk in chunks:
                    all_data.append(chunk)

                    # 中断チェック
                    event, values = window.read(timeout=0)
                    if event in [sg.WIN_CLOSED, 'interrupt']:
                        self.is_interrupt = True
                        return None

            except Exception as e:
                com.log('エラー: ' + file + ' - ' + str(e), lv='W')
                continue

        if 0 == len(all_data):
            return None

        # 全データを結合
        df = pd.concat(all_data, ignore_index=True)
        com.log(pair + ': ' + str(len(df)) + '行読み込み')

        # 日時カラムを作成
        df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + df['Time'].astype(str),
                                        format='%Y%m%d%H:%M:%S')

        # 土日を除外 (weekday: 5=土曜, 6=日曜)
        df = df[df['DateTime'].dt.weekday < 5]
        com.log(pair + ': 土日除外後 ' + str(len(df)) + '行')

        # 1時間足にリサンプル (Bidを使用)
        df = df.set_index('DateTime')
        df_h1 = df['Bid'].resample('H').agg(['first', 'max', 'min', 'last'])
        df_h1.columns = ['Open', 'High', 'Low', 'Close']

        # NaNを除外
        df_h1 = df_h1.dropna()

        # インデックスをリセットしてDateTime列を追加
        df_h1 = df_h1.reset_index()

        com.log(pair + ': 1時間足 ' + str(len(df_h1)) + '行')
        return df_h1

    def create_h1_d1(self):
        """BaseデータからH1・D1の終値データを作成"""
        if com.question('BaseデータからH1・D1(終値)を作成しますか？', '開始確認') <= 0:
            return

        start_time = com.time_start()

        # Baseフォルダのファイル一覧
        base_files = glob.glob(OUT_BASE_PATH + '/*.csv')
        others_files = glob.glob(OUT_BASE_PATH + '/others/*.csv')
        all_files = base_files + others_files

        if 0 == len(all_files):
            com.dialog(OUT_BASE_PATH + ' にファイルが存在しません。', title='ファイル不在', lv='w')
            return

        # 進捗表示
        window = com.progress('H1・D1(終値)作成中',
                              ['ファイル', len(all_files)], interrupt=True)
        event, values = window.read(timeout=0)

        try:
            for i, file in enumerate(sorted(all_files)):
                if self.is_interrupt:
                    break

                pair = os.path.basename(file).replace('.csv', '')
                is_others = '/others/' in file

                window['ファイル'].update(pair + ' (' + str(i + 1) + ' / ' + str(len(all_files)) + ')')
                window['ファイル_'].update(i + 1)

                try:
                    # Baseファイルを読み込み
                    df = pd.read_csv(file)
                    df['DateTime'] = pd.to_datetime(df['DateTime'])

                    # H1: 1時間足終値
                    df_h1 = df[['DateTime', 'Close']].copy()
                    h1_path = self._get_output_path(pair, OUT_H1_PATH, is_others)
                    df_h1.to_csv(h1_path, index=False)
                    com.log('H1出力: ' + h1_path + ' (' + str(len(df_h1)) + '行)')

                    # D1: 日足終値 (日毎の最終行を取得)
                    df['Date'] = df['DateTime'].dt.date
                    df_d1 = df.groupby('Date').last()[['Close']].reset_index()
                    df_d1.columns = ['Date', 'Close']
                    d1_path = self._get_output_path(pair, OUT_D1_PATH, is_others)
                    df_d1.to_csv(d1_path, index=False)
                    com.log('D1出力: ' + d1_path + ' (' + str(len(df_d1)) + '行)')

                except Exception as e:
                    com.log('エラー: ' + pair + ' - ' + str(e), lv='W')

                # 中断イベント
                event, values = window.read(timeout=0)
                if _is_interrupt(window, event):
                    self.is_interrupt = True
                    break

        finally:
            try:
                window.close()
            except:
                pass

        run_time = com.time_end(start_time)
        self.total_time += run_time
        com.log('H1・D1作成' + ('中断' if self.is_interrupt else '完了') +
                '(' + com.conv_time_str(run_time) + ')')
        com.dialog('H1・D1作成' + ('中断' if self.is_interrupt else '完了') +
                   'しました。(' + com.conv_time_str(run_time) + ')', 'H1・D1作成')

    def _get_output_path(self, pair, base_path, is_others=None):
        """出力パスを決定（対象通貨かothersか）"""
        if is_others is None:
            # 通貨ペアから通貨コードを抽出してチェック
            is_target = any(cur in pair for cur in TARGET_CURRENCIES)
            is_others = not is_target

        if is_others:
            others_path = base_path + '/others'
            os.makedirs(others_path, exist_ok=True)
            return others_path + '/' + pair + '.csv'
        else:
            return base_path + '/' + pair + '.csv'


def _is_interrupt(window, event):
    """中断イベントチェック"""
    if event in [sg.WIN_CLOSED, 'interrupt']:
        window.close()
        return True
    return False
