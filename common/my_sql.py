#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import mysql.connector as db


class MySql:

    def __init__(self, dbname):
        cnx = None

        # 接続情報をセット
        info = cst.MENU_CSV['Sql']
        info = info[(dbname == info['DBNAME'])]

        host_series = info['HOST'].values
        user_series = info['USER'].values
        pw_series = info['PASS'].values
        host = host_series[0]
        user = user_series[0]
        pw = pw_series[0]

        try:
            cnx = db.connect(host=host, user=user, password=pw, auth_plugin='mysql_native_password')
            com.log('MySQL: 接続 [' + host + '(' + dbname + ')]')

            cursor = cnx.cursor()
            cursor.execute('USE {}'.format(dbname))

        except Exception as e:
            com.log('MySQL: 接続エラー [' + host + '(' + dbname + ')] ' + str(e), 'E')
            cnx = None

        self.cnx = cnx

    def select(self, columns, table, where='', others='', as_dict=False):
        """
        SELECTクエリを実行

        Parameters:
        -----------
        columns: str
            取得する列名（カンマ区切り、または '*'）
        table: str
            テーブル名
        where: str
            WHERE句の条件
        others: str
            その他のSQL句（ORDER BY, LIMIT等）
        as_dict: bool
            True の場合、結果を辞書のリストで返す（列名でアクセス可能）
            False の場合、従来の形式 [列名リスト, データリスト] で返す

        Returns:
        --------
        as_dict=True: list of dict
            [{列名: 値, ...}, ...]
        as_dict=False: list
            [[列名1, 列名2, ...], [[値1, 値2, ...], ...]]
        """
        # SELECTデータ取得
        sql = 'SELECT ' + columns + ' FROM ' + table
        sql += (' WHERE ' + where if 0 < len(where) else '') + (' ' + others if 0 < len(others) else '')

        try:
            # 辞書形式で取得する場合
            cursor = self.cnx.cursor(dictionary=as_dict)
            cursor.execute(sql)
            result = cursor.fetchall()
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return [] if as_dict else ['', '']

        com.log('SQL: ' + sql.replace('\n', ' '))

        # 辞書形式の場合はそのまま返す
        if as_dict:
            return result

        # 従来の形式（互換性維持）
        # 列名取得
        sql_desc = 'DESC ' + table
        try:
            cursor_desc = self.cnx.cursor()
            cursor_desc.execute(sql_desc)
            show_cols = cursor_desc.fetchall()
        except Exception as e:
            com.log('SQLエラー: ' + sql_desc.replace('\n', ' ') + ', ' + str(e), 'E')
            return '', ''

        cols = [[col_tuple[0] for col_tuple in show_cols]]
        res = [[value for value in row] for row in result]
        cols.append(res)
        return cols

    def insert(self, columns, values, table):
        """
        パラメータ化クエリを使用したINSERT
        columns: 列名のリスト
        values: 値のリスト（複数行の場合はリストのリスト）
        table: テーブル名
        """
        # 列名は識別子なのでパラメータ化できない（文字列結合）
        column_str = ",".join([col for col in columns])
        # プレースホルダーを作成
        placeholders = ",".join(['%s'] * len(columns))
        sql = f'INSERT INTO {table} ({column_str}) VALUES ({placeholders})'

        try:
            cursor = self.cnx.cursor()
            # 複数行の場合は executemany を使用
            first_value = values[0]
            if isinstance(first_value, (list, tuple)):
                cursor.executemany(sql, values)
            else:
                cursor.execute(sql, values)
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return False

        com.log('SQL: ' + sql.replace('\n', ' '))
        return True

    def update(self, columns, values, table, where):
        """
        パラメータ化クエリを使用したUPDATE
        columns: 列名のリスト
        values: 値のリスト
        table: テーブル名
        where: WHERE句の条件（文字列）
        注意: WHERE句は文字列結合のため、呼び出し側で安全な値を渡すこと
        """
        # SET句をパラメータ化
        set_clause = ",".join([f'{col} = %s' for col in columns])
        sql = f'UPDATE {table} SET {set_clause} WHERE {where}'

        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql, values)
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return False

        com.log('SQL: ' + sql.replace('\n', ' '))
        return True

    def delete(self, table, where=''):
        """
        DELETE文の実行
        table: テーブル名
        where: WHERE句の条件（文字列、オプション）
        注意: WHERE句は文字列結合のため、呼び出し側で安全な値を渡すこと
        """
        sql = f'DELETE FROM {table}' + ('' if 0 == len(where) else f' WHERE {where}')
        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return False

        com.log('SQL: ' + sql.replace('\n', ' '))
        return True

    def free(self, sql, as_dict=False):
        """
        任意のSQLを実行

        Parameters:
        -----------
        sql: str
            SQL文（文字列）
        as_dict: bool
            True の場合、SELECT結果を辞書のリストで返す（列名でアクセス可能）

        警告: SQLインジェクションのリスクがあるため、外部入力を含むSQLは実行しないこと
        """
        com.log('SQL(Free): ' + sql.replace('\n', ' '))
        try:
            cursor = self.cnx.cursor(dictionary=as_dict)
            cursor.execute(sql)
            result = cursor.fetchall()
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return [] if as_dict else ''

        return result

    def close(self):
        try:
            self.cnx.close()
            com.log('MySQL: 切断')
        except (AttributeError, Exception) as e:
            com.log(f'MySQL切断エラー: {str(e)}', 'W')

    def commit(self):
        try:
            self.cnx.commit()
            com.log('SQL: コミット')
            return True
        except Exception as e:
            com.log('MySQL: コミット失敗', 'W')
            self.rollback()
        return False

    def rollback(self):
        try:
            self.cnx.rollback()
            com.log('MySQL: ロールバック', 'E')
            return True
        except Exception as e:
            com.log('MySQL: ロールバック失敗, ' + str(e), 'E')
        return False
