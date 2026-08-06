# FX Data Extraction to Excel

MySQLデータベース `fx_saya365` の rate と swap テーブルから全データを抽出し、DATE列で結合してExcelファイルの saya365 シートに書き込みます。

## 必要な環境

- macOS（AppleScriptを使用）
- Python 3.6以上
- Microsoft Excel for Mac
- 必要なパッケージ:
  - mysql-connector-python
  - pandas

## 特徴

- **直接Excel書き込み**: CSVファイルを経由せず、AppleScript経由でExcelに直接書き込み
- **既存ファイル更新**: 資産管理.xlsm の saya365 シートにデータを書き込み
- **mysql.connector使用**: 標準のmysql-connector-pythonを使用（MyToolの依存なし）

## インストール

### 1. Pythonパッケージのインストール

```bash
pip3 install mysql-connector-python pandas
```

## 使用方法

### スクリプトの実行

```bash
python3 extract_fx_to_excel.py
```

## 処理内容

1. データベース接続: `free-liberty.com:3306`
2. データベース: `fx_saya365`
3. 対象テーブル: **rate** と **swap**
4. 各テーブルから以下のカラムを抽出:
   - DATE (必須)
   - USDJPY
   - TRYJPY
   - HKDJPY
5. 通貨カラムにテーブル名のプレフィックスを追加:
   - rate_USDJPY, rate_TRYJPY, rate_HKDJPY
   - swap_USDJPY, swap_TRYJPY, swap_HKDJPY
6. DATE列で外部結合（OUTER JOIN）
7. AppleScript経由でExcelに書き込み
   - ファイル: `/Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data/資産管理.xlsm`
   - シート: `saya365`

## 出力

- **Excelファイル**: `資産管理.xlsm`
- **シート名**: `saya365`
- **データ**: 既存データはクリアされ、新しいデータが書き込まれます
- **カラム構成**:
  - DATE
  - rate_USDJPY, rate_TRYJPY, rate_HKDJPY
  - swap_USDJPY, swap_TRYJPY, swap_HKDJPY

## 動作仕組み

1. **データ抽出**: mysql.connectorでデータベースに接続し、pandasでデータを取得
2. **データ結合**: rate と swap テーブルを DATE 列でマージ
3. **Excel書き込み**: AppleScriptでMicrosoft Excelを操作
   - 既存の saya365 シートをクリア（なければ作成）
   - ヘッダー行と全データを書き込み
   - ブックを保存

## 注意事項

- **macOS専用**: AppleScriptを使用するため、macOSでのみ動作します
- **Excel起動**: スクリプト実行中にExcelが自動的に起動します
- **既存データ**: saya365 シートの既存データは完全に置き換えられます
- **ファイル存在確認**: 資産管理.xlsm が指定パスに存在する必要があります
- **データベース接続**: インターネット接続が必要です

## トラブルシューティング

### Excelファイルが見つからない

```
✗ Excel file not found: /Users/dsk_nagaoka/.../資産管理.xlsm
```

→ ファイルパスを確認し、ファイルが存在することを確認してください

### AppleScript実行エラー

```
✗ AppleScript error: ...
```

→ Microsoft Excel for Mac がインストールされていることを確認してください
→ Excelファイルが他のプログラムで開かれていないか確認してください

### データベース接続エラー

```
✗ MySQL Error: 2003: Can't connect to MySQL server
```

→ インターネット接続を確認してください
→ データベースサーバーが稼働中か確認してください

## 実行例

```
======================================================================
FX Data Extraction to Excel
======================================================================
Database: fx_saya365
Tables: rate, swap
Excel: 資産管理.xlsm
Sheet: saya365
======================================================================

✓ Excel file found: /Users/dsk_nagaoka/.../資産管理.xlsm

Connecting to database: fx_saya365
✓ Connected to database: fx_saya365

[1/2] Processing table: rate
  Available columns: DATE, USDJPY, TRYJPY, HKDJPY
  ✓ Extracted 1250 records from rate
    Columns: DATE, rate_USDJPY, rate_TRYJPY, rate_HKDJPY
    Date range: 2020-01-01 to 2026-08-06

[2/2] Processing table: swap
  Available columns: DATE, USDJPY, TRYJPY, HKDJPY
  ✓ Extracted 1250 records from swap
    Columns: DATE, swap_USDJPY, swap_TRYJPY, swap_HKDJPY
    Date range: 2020-01-01 to 2026-08-06

Merging tables on DATE column...
  Base: rate (1250 records)
  + swap (1250 records)

✓ Merged result: 1250 records
  Columns: DATE, rate_USDJPY, rate_TRYJPY, rate_HKDJPY, swap_USDJPY, swap_TRYJPY, swap_HKDJPY
  Date range: 2020-01-01 to 2026-08-06

Writing data to Excel: /Users/dsk_nagaoka/.../資産管理.xlsm
Sheet: saya365
Executing AppleScript to write to Excel...
✓ Successfully wrote 1250 rows to saya365 sheet

======================================================================
SUMMARY
======================================================================
Tables processed: 2
Total records: 1250
Excel file: /Users/dsk_nagaoka/.../資産管理.xlsm
Sheet: saya365
======================================================================

✓ Database connection closed
```
