#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
JSON API definition.
'''

import json, functools, re
import web
from base import utils
from status import *
from base.log import logger

__all__ = ["Page", "APIError", "APIValueError", "APIResourceNotFoundError",
           "APIPermissionError", "api", "input_data", "input_param", "assert_not_empty",
           "assert_int", "assert_float", "assert_passwd", "assert_phone",
           "assert_pcode"]


class Page(object):
    '''
    Page object for display pages.
    '''

    def __init__(self, item_count, page_index=0, page_size=15):
        '''
        Init Pagination by item_count, page_index and page_size.
        '''
        page_index += 1
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
        if (item_count == 0) or (page_index < 1) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size
        self.has_next = 1 if self.page_index < self.page_count else 0
        self.has_previous = 1 if self.page_index > 1 else 0

    def __str__(self):
        return 'item_count: %s, page_count: %s, page_index: %s, page_size: %s, offset: %s, limit: %s' % (
            self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)

    __repr__ = __str__


def loads(data):
    def _obj_hook(pairs):
        o = utils.Dict()
        for k, v in pairs.iteritems():
            o[str(k)] = v
        return o

    return json.loads(data, encoding="utf-8", object_hook=_obj_hook)


def _dump(obj):
    if isinstance(obj, Page):
        return {
            'has_more': obj.has_next
        }
    raise TypeError('%s is not JSON serializable' % obj)


def dumps(obj):
    return json.dumps(obj, default=_dump)


class APIError(StandardError):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''

    def __init__(self, error_code, message=''):
        super(APIError, self).__init__(message)
        self.error_code = error_code
        self.message = '%s. %s' % (STATUS_CODE[error_code], message)


class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''

    def __init__(self, message=''):
        super(APIValueError, self).__init__(CODE_VALUE_INVALID, message)


class APIResourceNotFoundError(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''

    def __init__(self, field, message=''):
        super(APIResourceNotFoundError, self).__init__(CODE_NOT_FOUND, message)


class APIPermissionError(APIError):
    '''
    Indicate the api has no permission.
    '''

    def __init__(self, message=''):
        super(APIPermissionError, self).__init__(CODE_FORBIDDEN, message)


def _encode_utf8(**kw):
    '''

    encode dict to json
    :param kw:
    :return:
    '''
    params = dict()
    for k, v in kw.iteritems():
        if isinstance(v, basestring):
            qv = v.encode('utf-8') if isinstance(v, unicode) else v
            params[str(k)] = qv
        elif isinstance(v, dict):
            params[str(k)] = _encode_utf8(**v)
        elif isinstance(v, list):
            sub = list()
            for i in v:
                if isinstance(i, dict):
                    qv = _encode_utf8(**i)
                elif isinstance(i, basestring):
                    qv = i.encode('utf-8') if isinstance(i, unicode) else i
                elif isinstance(i, list):
                    # not impl (our server not have this case)
                    pass
                else:
                    qv = i
                sub.append(qv)
            params[str(k)] = sub
        else:
            params[str(k)] = v
    return params


def input_data(**kw):
    '''
    request data
    :return:
    '''
    copy = loads(web.data())
    if kw:
        for k, v in kw.iteritems():
            if not k in copy:
                copy[k] = v
    logger.info("recv url: %s data: %s" % (web.ctx.path, copy))
    return copy


def input_param(**kw):
    '''
    :param kw:
    :return:
    '''
    copy = utils.Dict(**web.input(_unicode=False))
    if kw:
        for k, v in kw.iteritems():
            if not k in copy:
                copy[k] = v
    logger.info("recv url: %s data: %s" % (web.ctx.path, copy))
    return copy


def api(func):
    '''
    A decorator that makes a function to json api, makes the return value as json.

    @api
    def api_test():
        return dict(result='123', items=[])
    '''

    @functools.wraps(func)
    def _wrapper(*args, **kw):
        try:
            resp_obj = utils.Dict(rtn=CODE_SUCCESS, msg=STATUS_CODE[CODE_SUCCESS])
            resp = func(*args, **kw)
            if resp:
                resp_obj.result = resp
            r = json.dumps(_encode_utf8(**resp_obj), ensure_ascii=False)
        except APIError, e:
            error_obj = _encode_utf8(rtn=e.error_code, msg=e.message)
            r = json.dumps(error_obj, ensure_ascii=False)
        except Exception, e:
            # raise
            error_obj = _encode_utf8(rtn=CODE_INTERNAL_ERROR, msg='[%s]%s' % (e.__class__.__name__, e.message))
            r = json.dumps(error_obj, ensure_ascii=False)
        web.header('Content-Type', 'application/json;charset=utf-8')
        logger.info("resp data: %s" % r)
        return r

    return _wrapper


def assert_not_empty(text, name):
    if not text:
        raise APIValueError("%s is empty" % name)
    return text


def assert_int(s, name):
    try:
        return int(s)
    except ValueError:
        raise APIValueError("%s is invalid integer" % name)


def assert_float(s, name):
    try:
        return float(s)
    except ValueError:
        raise APIValueError("%s is invalid float" % name)


_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')


def assert_md5_passwd(passwd):
    pw = str(passwd)
    if _RE_MD5.match(pw) is None:
        raise APIValueError("invalid passwd")
    return pw


def assert_passwd(passwd):
    if len(passwd) < 6:
        raise APIValueError("invalid passwd")
    return passwd


_RE_PCODE = re.compile(r'^[0-9]{4}$')


def assert_pcode(code):
    pcode = str(code)
    if _RE_PCODE.match(pcode) is None:
        raise APIError(CODE_PCODE_VERIFY_FAILED, '')
    return pcode


_RE_PHONE = re.compile(r'^1\d{10}$')


def assert_phone(phone):
    phone = str(phone)
    if _RE_PHONE.match(phone) is None:
        raise APIValueError("invalid phone")
    return phone


if __name__ == '__main__':
    p = Page(100)
    # print p.item_count
    # print p.limit
    # print p.offset
    # print p.page_count
    # print p.page_index
    # print p.page_size

    t = {
        'a': 'aon',
        'b': {
            'c': 33
        }
    }

    datas = {'result': [{
        'love': u'我爱你',
        'array' : [
            {
                'good': u'好的',
            },
            {
                'good': u'坏的'
            }
        ]
    }]}

    print _encode_utf8(**datas)

    # print json.dumps(_encode_utf8(**datas), ensure_ascii=False)

