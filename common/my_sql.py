#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import com
from const import cst

import mysql.connector as db


class MySql:

    def __init__(self, host, dbname, user, pw):
        cnx = None
        try:
            cnx = db.connect(host=host, user=user, password=pw)
            com.log('MySQL: 接続 [' + host + '(' + dbname + ')]')

            cursor = cnx.cursor()
            cursor.execute('USE {}'.format(dbname))

        except Exception as e:
            com.log('MySQL: 接続エラー [' + host + '(' + dbname + ')] ' + str(e), 'E')
            self.cnx = None

        self.cnx = cnx

    def select(self, columns, table, where='', others=''):

        # 列名取得
        sql = 'DESC ' + table
        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
            show_cols = cursor.fetchall()
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return '', ''

        # SELECTデータ取得
        sql = 'SELECT ' + columns + ' FROM ' + table
        sql += (' WHERE ' + where if 0 < len(where) else '') + (' ' + others if 0 < len(others) else '')
        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return '', ''

        cols = [[col[0] for col in show_cols]]
        res = [[row for row in rows] for rows in result][0]

        cols.append(res)
        com.log('SQL: ' + sql.replace('\n', ' '))
        return cols

    def insert(self, columns, values, table):

        sql = 'INSERT INTO ' + table + ' (' + ",".join([col for col in columns]) + ') '
        sql += 'VALUES ' + ",".join(['(' + ",".join(['\'' + str(val) + '\'' for val in rows]) + ')' for rows in values])

        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return False

        com.log('SQL: ' + sql.replace('\n', ' '))
        return True

    def update(self, columns, values, table, where):

        sql = 'UPDATE ' + table + ' SET '
        sql += ",".join([columns[i] + ' = \'' + values[i] + '\'' for i in range(0, values)]) + ' WHERE ' + where
        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return False

        com.log('SQL: ' + sql.replace('\n', ' '))
        return True

    def delete(self, table, where):

        sql = 'DELETE FROM ' + table + ' WHERE ' + where
        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return False

        com.log('SQL: ' + sql.replace('\n', ' '))
        return True

    def free(self, sql):

        com.log('SQL(Free): ' + sql.replace('\n', ' '))
        try:
            cursor = self.cnx.cursor()
            cursor.execute(sql)
            result = cursor
        except Exception as e:
            com.log('SQLエラー: ' + sql.replace('\n', ' ') + ', ' + str(e), 'E')
            return ''

        return result

    def close(self):
        try:
            self.cnx.close()
            com.log('MySQL: 切断')
        except: pass

    def commit(self):
        self.cnx.commit()
        com.log('SQL: コミット')

    def rollback(self):
        self.cnx.rollback()
        com.log('MySQL: ロールバック')
