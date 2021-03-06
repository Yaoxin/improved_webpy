#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Database operation module.
'''

import time
from log import logger

import db

_engine = None


def create_engine(user, password, database, host="127.0.0.1", port=3306):
    global _engine
    if _engine is not None:
        raise db.DBError("The engine is already initialization.")

    _engine = db.Database(host, database, port, user, password)
    logger.info("Init mysql engine <%s> OK." % hex(id(_engine)))


class Field(object):
    _count = 0

    def __init__(self, **kw):
        self.name = kw.get('name', None)
        self._default = kw.get('default', None)
        self.primary_key = kw.get('primary_key', False)
        self.nullable = kw.get('nullable', False)
        self.updatable = kw.get('updatable', True)
        self.insertable = kw.get('insertable', True)
        self.autoable = kw.get('autoable', False)
        self.unique_key = kw.get('unique_key', False)
        self.normal_key = kw.get('normal_key', False)
        self.ddl = kw.get('ddl', '')
        self._order = Field._count
        Field._count += 1

    @property
    def default(self):
        d = self._default
        return d() if callable(d) else d

    def __str__(self):
        s = ['<%s:%s,%s,default(%s),' % (self.__class__.__name__, self.name, self.ddl, self._default)]
        self.nullable and s.append('N')
        self.updatable and s.append('U')
        self.insertable and s.append('I')
        s.append('>')
        return ''.join(s)


class StringField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['ddl'] = 'varchar(255)'
        super(StringField, self).__init__(**kw)


class IntegerField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'int(11)'
        super(IntegerField, self).__init__(**kw)


class CharField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['dd1'] = 'char(32)'
        super(CharField, self).__init__(**kw)


class FloatField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0.0
        if not 'ddl' in kw:
            kw['ddl'] = 'real'
        super(FloatField, self).__init__(**kw)


class BooleanField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = False
        if not 'ddl' in kw:
            kw['ddl'] = 'bool'
        super(BooleanField, self).__init__(**kw)


class TextField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['ddl'] = 'text'
        super(TextField, self).__init__(**kw)


class BlobField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['ddl'] = 'blob'
        super(BlobField, self).__init__(**kw)


class VersionField(Field):
    def __init__(self, name=None):
        super(VersionField, self).__init__(name=name, default=0, ddl='bigint')


_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])


def _gen_sql(table_name, mappings):
    pk = None
    keys = list()
    sql = ['-- generating SQL for %s:' % table_name, 'create table `%s` (' % table_name]
    for f in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
        if not hasattr(f, 'ddl'):
            raise StandardError('no ddl in field "%s".' % f.name)
        ddl = f.ddl
        nullable = f.nullable
        autoable = f.autoable
        if f.primary_key:
            pk = f.name
        if f.unique_key:
            keys.append(f.name)
        elif f.normal_key:
            keys.append(f.name)
        else:
            pass
        sql.append(' `%s` %s' % (f.name, ddl))
        if not nullable:
            sql.append(' not null')
        if autoable:
            sql.append(' auto_increment')
        sql.append(',')
    sql.append('  primary key(`%s`),' % pk)
    for key in keys:
        sql.append('  key `%s`(`%s`),' % (key, key))
    sql.append(');')
    return '\n'.join(sql)


class ModelMetaclass(type):
    '''
    Metaclass for model objects.
    '''

    def __new__(cls, name, bases, attrs):
        # skip base Model class:
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        # store all subclasses info:
        if not hasattr(cls, 'subclasses'):
            cls.subclasses = {}
        if not name in cls.subclasses:
            cls.subclasses[name] = name
        else:
            logger.warning('Redefine class: %s' % name)

        logger.debug('Scan ORMapping %s...' % name)
        mappings = dict()
        primary_key = None
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                if not v.name:
                    v.name = k
                logger.debug('Found mapping: %s => %s' % (k, v))
                # check duplicate primary key:
                if v.primary_key:
                    if primary_key:
                        raise TypeError('Cannot define more than 1 primary key in class: %s' % name)
                    primary_key = v
                if v.normal_key or v.primary_key or v.unique_key:
                    if v.updatable:
                        logger.warning('NOTE : the field change to non-updatable.')
                        v.updatable = False
                    if v.nullable:
                        logger.warning('NOTE : the field change to non-nullable')
                        v.nullable = False
                    if v.autoable:
                        logger.warning('NOTE: auto primary key to non-insertable.')
                        v.insertable = False
                mappings[k] = v
        # check exist of primary key:
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)
        for k in mappings.iterkeys():
            attrs.pop(k)
        if not '__table__' in attrs:
            attrs['__table__'] = name.lower()
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'], mappings)
        for trigger in _triggers:
            if not trigger in attrs:
                attrs[trigger] = None
        return type.__new__(cls, name, bases, attrs)


class Model(dict):
    '''
    Base class for ORM.

    -- generating SQL for user:
    create table `user` (
      `id` bigint not null,
      `name` varchar(255) not null,
      `email` varchar(255) not null,
      `passwd` varchar(255) not null,
      `last_modified` real not null,
      primary key(`id`)
    );
    '''
    __metaclass__ = ModelMetaclass

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def get(cls, pk):
        '''
        Get by primary key.
        '''
        d = _engine.select_one('select * from %s where %s=?' % (cls.__table__, cls.__primary_key__.name), pk)
        return cls(**d) if d else None

    @classmethod
    def find_first(cls, where, *args):
        '''
        Find by where clause and return one result. If multiple results found,
        only the first one returned. If no result found, return None.
        '''
        d = _engine.select_one('select * from %s %s' % (cls.__table__, where), *args)
        return cls(**d) if d else None

    @classmethod
    def find_all(cls, *args):
        '''
        Find all and return list.
        '''
        L = _engine.select('select * from `%s`' % cls.__table__)
        return [cls(**d) for d in L]

    @classmethod
    def find_by(cls, where, *args):
        '''
        Find by where clause and return list.
        '''
        L = _engine.select('select * from `%s` %s' % (cls.__table__, where), *args)
        return [cls(**d) for d in L]

    @classmethod
    def count_all(cls):
        '''
        Find by 'select count(pk) from table' and return integer.
        '''
        return _engine.select_int('select count(`%s`) from `%s`' % (cls.__primary_key__.name, cls.__table__))

    @classmethod
    def count_by(cls, where, *args):
        '''
        Find by 'select count(pk) from table where ... ' and return int.
        '''
        return _engine.select_int('select count(`%s`) from `%s` %s' % (cls.__primary_key__.name, cls.__table__, where),
                                  *args)

    @classmethod
    def last_insert_id(cls):
        '''
        :return: lastest insert id
        '''
        return _engine.get_last_insert_id().values()[0]

    @classmethod
    def find_original(cls, orm, sql, *args):
        if orm:
            L = _engine.select(sql, *args)
            return [cls(**d) for d in L]
        else:
            return _engine.select_join(sql, *args)

    def update(self):
        self.pre_update and self.pre_update()
        L = []
        args = []
        for k, v in self.__mappings__.iteritems():
            if v.updatable:
                if hasattr(self, k):
                    arg = getattr(self, k)
                else:
                    arg = v.default
                    setattr(self, k, arg)
                L.append('`%s`=?' % k)
                args.append(arg)
        pk = self.__primary_key__.name
        args.append(getattr(self, pk))
        _engine.update('update `%s` set %s where %s=?' % (self.__table__, ','.join(L), pk), *args)
        return self

    def delete(self):
        self.pre_delete and self.pre_delete()
        pk = self.__primary_key__.name
        args = (getattr(self, pk),)
        _engine.update('delete from `%s` where `%s`=?' % (self.__table__, pk), *args)
        return self

    def insert(self):
        self.pre_insert and self.pre_insert()
        params = {}
        for k, v in self.__mappings__.iteritems():
            if v.insertable:
                if not hasattr(self, k):
                    setattr(self, k, v.default)
                params[v.name] = getattr(self, k)
        _engine.insert('%s' % self.__table__, **params)
        return self


if __name__ == '__main__':
    create_engine('root', '******', 'test')
    _engine.update('drop table if exists user')
    _engine.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
