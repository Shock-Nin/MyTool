# FX End-of-Month Data Extraction

このスクリプトは、MySQLデータベース `fx_saya365` から2025年12月以降の月末データを抽出し、CSVファイルとして出力します。

## 必要な環境

- Python 3.6以上
- MyToolプロジェクトの環境
- 必要なパッケージ:
  - mysql-connector-python
  - pandas

## 特徴

- **MyToolの既存MySQLクラスを使用**: `common/my_sql.py` のMySqlクラスを使用して接続
- **統一されたログ出力**: MyToolのログシステムと統合

## インストール

### 1. Pythonパッケージのインストール

```bash
pip install mysql-connector-python pandas
```

または

```bash
pip3 install mysql-connector-python pandas
```

## 使用方法

### スクリプトの実行

```bash
python extract_fx_end_of_month.py
```

または

```bash
python3 extract_fx_end_of_month.py
```

## 出力

- **出力先**: `/Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data`
- **ファイル形式**: `{テーブル名}_end_of_month.csv`
- **文字コード**: UTF-8 (BOM付き)

## 処理内容

1. データベース接続: `free-liberty.com:3306`
2. データベース: `fx_saya365`
3. 全テーブルをスキャン
4. 以下のカラムを含むテーブルからデータ抽出:
   - DATE (必須)
   - USDJPY
   - TRYJPY
   - HKD
   - JPY
5. 2025年12月1日以降のデータを抽出
6. 各月の最終日のデータのみをフィルタリング
7. CSVファイルとして出力

## 接続情報

- **Host**: free-liberty.com
- **Port**: 3306
- **User**: master
- **Database**: fx_saya365

## 注意事項

- データベースへの接続にはインターネット接続が必要です
- 出力先ディレクトリが存在しない場合は自動的に作成されます
- 同名のCSVファイルが存在する場合は上書きされます
- DATE カラムが存在しないテーブルはスキップされます
- 必要なカラムが2つ未満のテーブルもスキップされます

## トラブルシューティング

### 接続エラーが発生する場合

```
✗ MySQL Error: 2003: Can't connect to MySQL server
```

- インターネット接続を確認してください
- ファイアウォール設定を確認してください
- データベースサーバーが稼働中か確認してください

### パッケージのインストールエラー

macOSでpipのエラーが出る場合:

```bash
python3 -m pip install --user mysql-connector-python pandas
```

Windowsの場合:

```bash
py -m pip install mysql-connector-python pandas
```

## 実行例

```
======================================================================
FX End-of-Month Data Extraction
======================================================================
Database: free-liberty.com:3306/fx_saya365
Period: From December 2025 onwards
Output: /Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data
======================================================================

✓ Output directory ready: /Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data

✓ Connected to database: fx_saya365
✓ Found 5 tables

[1/5] Processing table: forex_data
  ✓ Extracted 8 end-of-month records from forex_data
    Columns: DATE, USDJPY, TRYJPY, HKD, JPY
  ✓ Exported to: /Users/dsk_nagaoka/.../forex_data_end_of_month.csv

...

======================================================================
SUMMARY
======================================================================
Tables processed: 5
Tables exported: 3
Total records: 24
Output location: /Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data
======================================================================

✓ Database connection closed
```
