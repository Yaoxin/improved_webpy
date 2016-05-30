#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = 'cloudy'


class Dict(dict):
    '''
    Simple dict but support access as x.y style.

    '''

    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def load_module(module_name):
    '''
    Load module from name as str.
    '''
    last_dot = module_name.rfind('.')
    if last_dot == (-1):
        return __import__(module_name, globals(), locals())
    from_module = module_name[:last_dot]
    import_module = module_name[last_dot + 1:]
    m = __import__(from_module, globals(), locals(), [import_module])
    return getattr(m, import_module)

