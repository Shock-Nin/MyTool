#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract FX data from fx_saya365 database
Merges rate and swap tables on DATE, outputs to saya365.csv
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.my_sql import MySql
from const import cst

# Output directory and filename
OUTPUT_DIR = '/Users/dsk_nagaoka/Library/CloudStorage/OneDrive-個人用/ドキュメント/Data'
OUTPUT_FILENAME = 'saya365.csv'

# Database name
DB_NAME = 'fx_saya365'

# Target tables
TARGET_TABLES = ['rate', 'swap']

# Required columns (excluding DATE)
CURRENCY_COLS = ['USDJPY', 'TRYJPY', 'HKDJPY']


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


def extract_table_data(mysql, table_name, columns):
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

        result = mysql.free(query)

        if not result:
            print(f"  ⊘ No data in {table_name}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(result, columns=available_cols)

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


def main():
    print("="*70)
    print("FX Data Extraction and Merge")
    print("="*70)
    print(f"Database: {DB_NAME}")
    print(f"Tables: {', '.join(TARGET_TABLES)}")
    print(f"Output: {OUTPUT_FILENAME}")
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
        # Extract data from all target tables
        dataframes = {}

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
            df = extract_table_data(mysql, table_name, columns)

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

        # Export to CSV
        output_file = os.path.join(OUTPUT_DIR_ACTUAL, OUTPUT_FILENAME)
        merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ Exported to: {output_file}")

        print("\n" + "="*70)
        print(f"SUMMARY")
        print("="*70)
        print(f"Tables processed: {len(dataframes)}")
        print(f"Total records: {len(merged_df)}")
        print(f"Output file: {output_file}")
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
