# FX Data Extraction

このスクリプトは、MySQLデータベース `fx_saya365` の rate と swap テーブルから全データを抽出し、CSVファイルとして出力します。

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
3. 対象テーブル: **rate** と **swap**
4. 以下のカラムを抽出:
   - DATE (必須)
   - USDJPY
   - TRYJPY
   - HKDJPY
5. 全期間のデータを抽出
6. CSVファイルとして出力
   - `rate.csv`
   - `swap.csv`

## 接続情報

- **Host**: free-liberty.com
- **Port**: 3306
- **User**: master
- **Database**: fx_saya365

## 注意事項

- データベースへの接続にはインターネット接続が必要です
- 出力先ディレクトリが存在しない場合は自動的に作成されます
- 同名のCSVファイルが存在する場合は上書きされます (`rate.csv`, `swap.csv`)
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
FX Data Extraction
======================================================================
Database: fx_saya365
Tables: rate, swap
Output: /Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data
======================================================================

✓ Output directory ready: /Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data

✓ Database configuration set up
Connecting to database: fx_saya365
MySQL: 接続 [free-liberty.com(fx_saya365)]

[1/2] Processing table: rate
  Available columns: DATE, USDJPY, TRYJPY, HKDJPY
  ✓ Extracted 1250 records from rate
    Columns: DATE, USDJPY, TRYJPY, HKDJPY
    Date range: 2020-01-01 to 2026-08-06
  ✓ Exported to: /Users/dsk_nagaoka/.../rate.csv

[2/2] Processing table: swap
  Available columns: DATE, USDJPY, TRYJPY, HKDJPY
  ✓ Extracted 1250 records from swap
    Columns: DATE, USDJPY, TRYJPY, HKDJPY
    Date range: 2020-01-01 to 2026-08-06
  ✓ Exported to: /Users/dsk_nagaoka/.../swap.csv

======================================================================
SUMMARY
======================================================================
Tables processed: 2
Tables exported: 2
Total records: 2500
Output location: /Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data
======================================================================

MySQL: 切断
```
