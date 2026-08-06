#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract FX data from fx_saya365 database
Exports data with DATE, USDJPY, TRYJPY, HKDJPY columns from rate and swap tables
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.my_sql import MySql
from const import cst

# Output directory
OUTPUT_DIR = '/Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data'

# Database name
DB_NAME = 'fx_saya365'

# Target tables
TARGET_TABLES = ['rate', 'swap']

# Required columns
REQUIRED_COLS = ['DATE', 'USDJPY', 'TRYJPY', 'HKDJPY']


def setup_db_config():
    """Setup database configuration in MENU_CSV if not already loaded."""
    if cst.MENU_CSV['Sql'] is None:
        # Create configuration DataFrame
        cst.MENU_CSV['Sql'] = pd.DataFrame([{
            'DBNAME': 'fx_saya365',
            'HOST': 'free-liberty.com',
            'USER': 'master',
            'PASS': 'Shock19800226!'
        }])
        print("✓ Database configuration set up")


def get_table_columns(mysql, table_name):
    """Get column names for a table."""
    try:
        result = mysql.free(f"SHOW COLUMNS FROM `{table_name}`")
        if not result:
            return []
        columns = [col[0] for col in result]
        return columns
    except Exception as e:
        print(f"✗ Error getting columns for {table_name}: {e}")
        return []


def extract_fx_data(mysql, table_name, columns):
    """Extract all FX data from a table."""
    try:
        # Build column list - check which required columns exist
        available_cols = [col for col in REQUIRED_COLS if col in columns]

        if 'DATE' not in available_cols:
            print(f"  ⊘ Skipping {table_name}: no DATE column")
            return None

        if len(available_cols) < 2:  # Need at least DATE and one other column
            print(f"  ⊘ Skipping {table_name}: insufficient required columns (has: {available_cols})")
            return None

        col_list = ', '.join([f'`{col}`' for col in available_cols])

        # Query to get all data
        query = f"""
        SELECT {col_list}
        FROM `{table_name}`
        ORDER BY `DATE`
        """

        result = mysql.free(query)

        if not result:
            print(f"  ⊘ No data in {table_name}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(result, columns=available_cols)

        if df.empty:
            print(f"  ⊘ No data in {table_name}")
            return None

        print(f"  ✓ Extracted {len(df)} records from {table_name}")
        print(f"    Columns: {', '.join(available_cols)}")

        # Show date range
        df_temp = df.copy()
        df_temp['DATE'] = pd.to_datetime(df_temp['DATE'])
        min_date = df_temp['DATE'].min()
        max_date = df_temp['DATE'].max()
        print(f"    Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")

        return df

    except Exception as e:
        print(f"  ✗ Error extracting data from {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("="*70)
    print("FX Data Extraction")
    print("="*70)
    print(f"Database: {DB_NAME}")
    print(f"Tables: {', '.join(TARGET_TABLES)}")
    print(f"Output: {OUTPUT_DIR}")
    print("="*70)
    print()

    # Create output directory if it doesn't exist
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"✓ Output directory ready: {OUTPUT_DIR}\n")
        OUTPUT_DIR_ACTUAL = OUTPUT_DIR
    except Exception as e:
        print(f"✗ Error creating output directory: {e}")
        print("  Using current directory instead")
        OUTPUT_DIR_ACTUAL = '.'

    # Setup database configuration
    setup_db_config()

    # Connect to database using MySql class
    print(f"Connecting to database: {DB_NAME}")
    mysql = MySql(DB_NAME)

    if mysql.cnx is None:
        print("\n✗ Failed to connect to database. Exiting.")
        return

    try:
        # Process target tables
        exported_count = 0
        total_records = 0

        for i, table_name in enumerate(TARGET_TABLES, 1):
            print(f"[{i}/{len(TARGET_TABLES)}] Processing table: {table_name}")

            # Get columns
            columns = get_table_columns(mysql, table_name)

            if not columns:
                print(f"  ⊘ Could not get columns for {table_name}")
                print()
                continue

            print(f"  Available columns: {', '.join(columns)}")

            # Extract data
            df = extract_fx_data(mysql, table_name, columns)

            if df is not None and not df.empty:
                # Export to CSV
                output_file = os.path.join(OUTPUT_DIR_ACTUAL, f"{table_name}.csv")
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"  ✓ Exported to: {output_file}")
                exported_count += 1
                total_records += len(df)

            print()

        print("="*70)
        print(f"SUMMARY")
        print("="*70)
        print(f"Tables processed: {len(TARGET_TABLES)}")
        print(f"Tables exported: {exported_count}")
        print(f"Total records: {total_records}")
        print(f"Output location: {OUTPUT_DIR_ACTUAL}")
        print("="*70)

    finally:
        mysql.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
