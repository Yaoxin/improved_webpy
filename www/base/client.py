#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
a simple http client for  server
'''

__version__ = '1.0.0'
__author__ = 'cloudy'

__all__ = ["Singleton", "ClientError", "JsonDict", "APIClient"]

import json, urllib, urllib2, time, collections


class Singleton:
    '''
    A non-thread-safe helper class to ease implementing singletons.
    '''

    def __init__(self, decorated, *args, **kw):
        self._decorated = decorated
        self._args = list(args)
        self._kw = dict(kw)

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated(*self._args, **self._kw)
            return self._instance

    def __call__(self, *args, **kwargs):
        raise TypeError("Singleton must be accessed through 'Instance' ")

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


class ClientError(StandardError):
    'raise APIError if receiving json message failure'

    def __init__(self, error_code, error, request):
        self.error_code = error_code
        self.error = error
        self.request = request

    def __str__(self):
        return 'errorcode=%s(msg=%s)----request:%s' % (self.error_code, self.error, self.request)


class JsonDict(dict):
    'general json object thash allow attributes to be bound to and behaves like a dict'

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise ArithmeticError("JsonDict key(%s) error." % key)

    def __setattr__(self, key, value):
        self[key] = value


def _parse_json(s):
    ' parse json to JsonDict '

    def _obj_hook(pairs):
        o = JsonDict()
        for k, v in pairs.iteritems():
            o[str(k)] = v
        return o

    return json.loads(s, object_hook=_obj_hook)


def _encode_param(**kw):
    args = list()
    for k, v in kw.iteritems():
        if isinstance(v, basestring):
            qv = v.encode('utf-8') if isinstance(v, unicode) else v
            args.append('%s=%s' % (k, urllib.quote(qv)))
        # array
        elif isinstance(v, collections.Iterable):
            for i in v:
                qv = i.encode('utf-8') if isinstance(i, unicode) else i
                args.append('%s=%s' % (k, urllib.quote(qv)))
        else:
            qv = str(v)
            args.append('%s=%s' % (k, qv))
    return '&'.join(args)


def _encode_json(**kw):
    ' encode dict to json '
    params = dict()
    for k, v in kw.iteritems():
        if isinstance(v, basestring):
            qv = v.encode('utf-8') if isinstance(v, unicode) else v
            params[str(k)] = qv
        elif isinstance(v, collections.Iterable):
            sub = list()
            for i in v:
                qv = i.encode('utf-8') if isinstance(i, unicode) else i
                sub.append(qv)
            params[str(k)] = sub
        else:
            params[str(k)] = v
    return json.dumps(params, ensure_ascii=False)


_HTTP_GET = 0
_HTTP_POST = 1

_API_VERSION = 2003


def _http_call(url, method, access_token, **kw):
    'general http call '
    if access_token:
        kw.update({'token': access_token})
    kw.update({'ver': _API_VERSION})
    params = None
    if method == _HTTP_GET:
        params = _encode_param(**kw)
    else:
        params = _encode_json(**kw)
    http_url = '%s?%s'(url, params) if method == _HTTP_GET else url
    http_body = None if method == _HTTP_GET else params
    req = urllib2.Request(http_url, http_body)
    try:
        resp = urllib2.urlopen(req, timeout=5)
        body = resp.read()
        r = _parse_json(body)
        if hasattr(r, 'rtn'):
            if r.rtn != 0:
                raise ClientError(str(r.rtn), r.msg, url)
            else:
                return r
        else:
            raise ClientError('009', 'response error', url)

    except urllib2.HTTPError, e:
        try:
            r = _parse_json(e)
        except:
            r = None
        if hasattr(r, 'rtn'):
            raise ClientError(str(r.rtn), r.msg, url)
        else:
            raise ClientError('009', 'response error', url)


@Singleton
class APIClient(object):
    '''
        API http client
        client = APIClient()
        res = client.member.login_API(phone='137****4567', passwd = '123456')
    '''

    def __init__(self, domain='localhost:8080', version=4):
        self.api_url = 'http://%s/api/v%d/' % (domain, version)
        self.access_token = ''
        self.expires = 0.0

    def __getattr__(self, attr):
        if '__' in attr:
            return getattr(attr)
        else:
            return _Callable(self, attr)

    def set_access_token(self, access_token):
        self.access_token = str(access_token)
        self.expires = time.time() + 86400.0

    def is_expired(self):
        # some api do not want token
        if not self.access_token:
            return False
        else:
            return time.time() > self.expires


class _Executable(object):
    def __init__(self, client, method, path):
        self.client = client
        self.method = method
        self.path = path

    def __call__(self, **kw):
        if self.client.is_expired():
            raise ClientError('119', 'token expired', '%s%s' % (self.client.api_url, self.path))
        else:
            return _http_call('%s%s' % (self.client.api_url, self.path), self.method,
                              self.client.access_token, **kw)

    def __str__(self):
        method = 'GET' if self.method == _HTTP_GET else _HTTP_POST
        return '_Executable: %s %s' % (method, self.path)

    __repr__ = __str__


class _Callable(object):
    def __init__(self, client, path):
        self.client = client
        self.path = path

    def __getattr__(self, attr):
        if attr == 'get':
            return _Executable(self.client, _HTTP_GET, self.path)
        elif attr == 'post':
            return _Executable(self.client, _HTTP_POST, self.path)
            pass
        else:
            return _Callable(self.client, '%s/%s' % (self.path, attr))

    def __str__(self):
        return '_Callable: %s' % self.path

    __repr__ = __str__


if __name__ == '__main__':
    client_A = APIClient.Instance()
    client_B = APIClient.Instance()

    print client_A is client_B
