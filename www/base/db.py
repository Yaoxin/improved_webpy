#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
a simple db connector ,with long connection
'''

__version__ = '1.0.1'
__author__ = 'cloudy'

import pymysql
import pymysql.cursors
import time, uuid
from log import logger

__all__ = ["Dict", "Database", "DBError", "DatabaseExecError", "MultiColumnsError"]


def next_id(t=None):
    '''
    :param t: unix timestamp ,default to None and using time.time()
    :return: next id as 50-char string.
    '''
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)


def _profiling(start, sql=''):
    t = time.time() - start
    if t > 0.1:
        logger.warning('[PROFILING] [DB] %s: %s' % (t, sql))
    else:
        logger.info('[PROFILING] [DB] %s: %s' % (t, sql))


class DBError(Exception):
    pass


class DatabaseExecError(DBError):
    pass


class MultiColumnsError(DBError):
    pass


class Dict(dict):
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, e:
            raise AttributeError, e


class Database(object):
    def __init__(self, host, db, port=3306, user='root', passwd='pure123', connect_timeout=3):
        self.host = host
        self.name = db
        self.port = port
        self.user = user
        self.passwd = passwd
        self.connect_timeout = connect_timeout
        self.connect_db()

    def connect_db(self):
        try:
            self.db = pymysql.connect(
                host=self.host,
                user=self.user,
                passwd=self.passwd,
                db=self.name,
                port=int(self.port),
                connect_timeout=self.connect_timeout,
                charset="utf8"
            )
            self.db.autocommit(True)

            return True
        except pymysql.Error, err:
            logger.error("CONNECT TO DB FAILED! ERR INFO: %s" % err)
            return False

    def reconnect_db(self):
        self.disconnect_db()
        return self.connect_db()

    def disconnect_db(self):
        try:
            self.db.close()
        except AttributeError, err:
            pass
        finally:
            logger.info("database connection closed!")

    def is_db_connected(self):
        try:
            self.db.ping()
            return True
        except pymysql.Error, err:
            logger.error("DB DISCONNECTED!Try to reconnect..., err info: %s"
                         % err)
        except AttributeError, err:
            logger.error("DB DISCONNECTED!Try to reconnect..., err info: %s"
                         % err)
        return False

    def _select(self, sql, first, *args):
        '''
        a litter issue: every mysql operate must ping ! how to slove it?
        '''
        cursor = None
        sql = sql.replace('?', '%s')
        logger.debug("%s" % sql)
        try:
            if self.is_db_connected() is False:
                raise DatabaseExecError()
            cursor = self.db.cursor()
            cursor.execute(sql, args)
            if cursor.description:
                names = [x[0] for x in cursor.description]
            if first:
                values = cursor.fetchone()
                if not values:
                    return None
                return Dict(names, values)
            return [Dict(names, x) for x in cursor.fetchall()]
        except pymysql.Error, err:
            logger.error("execute sql error,err info:%s, sql:%s" % (err, sql))
            self.disconnect_db()
            raise DatabaseExecError()
        finally:
            if cursor:
                cursor.close()

    def _select_join(self, sql, first, *args):
        cursor = None
        sql = sql.replace('?', '%s')
        logger.debug("%s" % sql)
        try:
            if self.is_db_connected() is False:
                raise DatabaseExecError()
            cursor = self.db.cursor()
            cursor.execute(sql, args)
            if first:
                values = cursor.fetchone()
                if not values:
                    return None
                return values
            return cursor.fetchall()
        except pymysql.Error, err:
            logger.error("execute sql error,err info:%s, sql:%s" % (err, sql))
            self.disconnect_db()
            raise DatabaseExecError()
        finally:
            if cursor:
                cursor.close()

        pass

    def select_int(self, sql, *args):
        d = self._select(sql, True, *args)
        if len(d) != 1:
            raise MultiColumnsError("Expect only one column.")
        return d.values()[0]

    def select_one(self, sql, *args):
        return self._select(sql, True, *args)

    def select(self, sql, *args):
        return self._select(sql, False, *args)

    def select_join(self, sql, *args):
        return self._select_join(sql, False, *args)

    def _update(self, sql, *args):
        cursor = None
        sql = sql.replace('?', '%s')
        logger.debug("%s" % sql)
        try:
            if self.is_db_connected() is False:
                raise DatabaseExecError()
            cursor = self.db.cursor()
            cursor.execute(sql, args)
            r = cursor.rowcount
            return r
        except pymysql.Error, err:
            logger.error("execute sql error, err info: %s, sql:%s" % (err, sql))
            self.disconnect_db()
            raise DatabaseExecError()
        finally:
            if cursor:
                cursor.close()

    def insert(self, table, **kw):
        cols, args = zip(*kw.iteritems())
        sql = "INSERT IGNORE INTO %s (%s) VALUES (%s)" % (table, ','.join(['`%s`' % col for col in cols]),
                                                          ','.join(['?' for i in range(len(cols))]))
        return self._update(sql, *args)

    def update(self, sql, *args):
        return self._update(sql, *args)

    def get_last_insert_id(self):
        return self._select("SELECT LAST_INSERT_ID()", True)


if __name__ == '__main__':
    pass

