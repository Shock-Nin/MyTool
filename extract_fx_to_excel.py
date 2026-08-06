#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract FX data from fx_saya365 database and write to Excel
Merges rate and swap tables on DATE, writes to saya365 sheet in 資産管理.xlsm
"""
import pandas as pd
from datetime import datetime
import subprocess
import os
import mysql.connector

# Excel file path
EXCEL_DIR = '/Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data'
EXCEL_FILENAME = '資産管理.xlsm'
SHEET_NAME = 'saya365'

# Database connection config
DB_CONFIG = {
    'host': 'free-liberty.com',
    'port': 3306,
    'user': 'master',
    'password': 'Shock19800226!',
    'database': 'fx_saya365'
}

# Target tables
TARGET_TABLES = ['rate', 'swap']

# Required columns (excluding DATE)
CURRENCY_COLS = ['USDJPY', 'TRYJPY', 'HKDJPY']


def connect_to_db():
    """Connect to MySQL database."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print(f"✓ Connected to database: {DB_CONFIG['database']}")
        return connection
    except mysql.connector.Error as err:
        print(f"✗ MySQL Error: {err}")
        return None
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return None


def get_table_columns(connection, table_name):
    """Get column names for a table."""
    try:
        cursor = connection.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        columns = [col[0] for col in cursor.fetchall()]
        cursor.close()
        return columns
    except Exception as e:
        print(f"✗ Error getting columns for {table_name}: {e}")
        return []


def extract_table_data(connection, table_name, columns):
    """Extract all data from a table."""
    try:
        # Check if DATE column exists
        if 'DATE' not in columns:
            print(f"  ⊘ Skipping {table_name}: no DATE column")
            return None

        # Build column list - DATE + available currency columns
        available_cols = ['DATE'] + [col for col in CURRENCY_COLS if col in columns]

        if len(available_cols) < 2:  # Need at least DATE and one currency column
            print(f"  ⊘ Skipping {table_name}: insufficient columns (has: {available_cols})")
            return None

        col_list = ', '.join([f'`{col}`' for col in available_cols])

        # Query to get all data
        query = f"""
        SELECT {col_list}
        FROM `{table_name}`
        ORDER BY `DATE`
        """

        df = pd.read_sql(query, connection)

        if df.empty:
            print(f"  ⊘ No data in {table_name}")
            return None

        # Convert DATE to datetime
        df['DATE'] = pd.to_datetime(df['DATE'])

        # Rename currency columns with table prefix (but not DATE)
        rename_dict = {col: f"{table_name}_{col}" for col in available_cols if col != 'DATE'}
        df = df.rename(columns=rename_dict)

        print(f"  ✓ Extracted {len(df)} records from {table_name}")
        print(f"    Columns: {', '.join(df.columns.tolist())}")

        # Show date range
        min_date = df['DATE'].min()
        max_date = df['DATE'].max()
        print(f"    Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

        return df

    except Exception as e:
        print(f"  ✗ Error extracting data from {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def write_to_excel(df, excel_path, sheet_name):
    """Write DataFrame to Excel using AppleScript."""
    print(f"\nWriting data to Excel: {excel_path}")
    print(f"Sheet: {sheet_name}")

    try:
        # Create AppleScript to write to Excel
        applescript = f'''
        tell application "Microsoft Excel"
            activate

            -- Open workbook
            set excelPath to "{excel_path}"
            set workbookOpen to false
            set targetWorkbook to missing value

            repeat with wb in workbooks
                if (full name of wb) is excelPath then
                    set workbookOpen to true
                    set targetWorkbook to wb
                    exit repeat
                end if
            end repeat

            if not workbookOpen then
                open excelPath
                set targetWorkbook to active workbook
            end if

            -- Get or create sheet
            set sheetExists to false
            try
                set targetSheet to worksheet "{sheet_name}" of targetWorkbook
                set sheetExists to true
            on error
                set targetSheet to make new worksheet at targetWorkbook with properties {{name:"{sheet_name}"}}
            end try

            -- Clear existing content
            if sheetExists then
                try
                    clear contents range "A:ZZ" of targetSheet
                end try
            end if

            -- Write headers and data
            set rowNum to 1
        '''

        # Add header row
        headers = df.columns.tolist()
        for col_idx, header in enumerate(headers, 1):
            applescript += f'''
            set value of cell {1} of column {col_idx} of targetSheet to "{header}"
            '''

        # Add data rows
        for row_idx, row in enumerate(df.itertuples(index=False), 2):
            for col_idx, value in enumerate(row, 1):
                # Convert value to string, handle None/NaN
                if pd.isna(value):
                    val_str = ""
                elif isinstance(value, pd.Timestamp):
                    val_str = value.strftime('%Y-%m-%d')
                else:
                    val_str = str(value)

                # Escape quotes in the value
                val_str = val_str.replace('"', '\\"')

                applescript += f'''
            set value of cell {row_idx} of column {col_idx} of targetSheet to "{val_str}"
                '''

        # Save and close
        applescript += '''

            -- Save workbook
            save targetWorkbook

            return "Success"
        end tell
        '''

        # Execute AppleScript
        print("Executing AppleScript to write to Excel...")
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"✓ Successfully wrote {len(df)} rows to {sheet_name} sheet")
            return True
        else:
            print(f"✗ AppleScript error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ AppleScript execution timed out")
        return False
    except Exception as e:
        print(f"✗ Error writing to Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("FX Data Extraction to Excel")
    print("="*70)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Tables: {', '.join(TARGET_TABLES)}")
    print(f"Excel: {EXCEL_FILENAME}")
    print(f"Sheet: {SHEET_NAME}")
    print("="*70)
    print()

    # Check if Excel file exists
    excel_path = os.path.join(EXCEL_DIR, EXCEL_FILENAME)
    if not os.path.exists(excel_path):
        print(f"✗ Excel file not found: {excel_path}")
        print("  Please ensure the file exists before running this script.")
        return

    print(f"✓ Excel file found: {excel_path}\n")

    # Connect to database
    print(f"Connecting to database: {DB_CONFIG['database']}")
    connection = connect_to_db()

    if connection is None:
        print("\n✗ Failed to connect to database. Exiting.")
        return

    try:
        # Extract data from all target tables
        dataframes = {}

        for i, table_name in enumerate(TARGET_TABLES, 1):
            print(f"[{i}/{len(TARGET_TABLES)}] Processing table: {table_name}")

            # Get columns
            columns = get_table_columns(connection, table_name)

            if not columns:
                print(f"  ⊘ Could not get columns for {table_name}")
                print()
                continue

            print(f"  Available columns: {', '.join(columns)}")

            # Extract data
            df = extract_table_data(connection, table_name, columns)

            if df is not None and not df.empty:
                dataframes[table_name] = df

            print()

        # Merge dataframes on DATE
        if len(dataframes) == 0:
            print("✗ No data extracted from any table")
            return

        print("Merging tables on DATE column...")

        # Start with the first dataframe
        merged_df = None
        for table_name, df in dataframes.items():
            if merged_df is None:
                merged_df = df
                print(f"  Base: {table_name} ({len(df)} records)")
            else:
                merged_df = pd.merge(merged_df, df, on='DATE', how='outer')
                print(f"  + {table_name} ({len(df)} records)")

        # Sort by DATE
        merged_df = merged_df.sort_values('DATE').reset_index(drop=True)

        print(f"\n✓ Merged result: {len(merged_df)} records")
        print(f"  Columns: {', '.join(merged_df.columns.tolist())}")

        # Show date range
        min_date = merged_df['DATE'].min()
        max_date = merged_df['DATE'].max()
        print(f"  Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

        # Write to Excel
        success = write_to_excel(merged_df, excel_path, SHEET_NAME)

        if success:
            print("\n" + "="*70)
            print(f"SUMMARY")
            print("="*70)
            print(f"Tables processed: {len(dataframes)}")
            print(f"Total records: {len(merged_df)}")
            print(f"Excel file: {excel_path}")
            print(f"Sheet: {SHEET_NAME}")
            print("="*70)
        else:
            print("\n✗ Failed to write data to Excel")

    finally:
        connection.close()
        print("\n✓ Database connection closed")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
