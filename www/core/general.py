#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = 'cloudy'

'''
    general function ...
'''
import datetime, random, hashlib, time, base64
from Crypto.Cipher import AES
from binascii import b2a_hex


def calc_age(birthday):
    try:
        ltime = time.localtime(birthday)
        age = datetime.datetime.today().year - ltime[0]
        return age if age > 0 else 0
    except Exception:
        return 0


def is_today(time_stamp):
    try:
        ltime = time.localtime(time_stamp)
        now_day = datetime.datetime.today()
        if now_day.year == ltime[0] and now_day.month == ltime[1] and now_day.day == ltime[2]:
            return True
        else:
            return False
    except Exception:
        return False


def generate_verify_num(length):
    assert isinstance(length, int)
    num_list = []
    for i in xrange(length):
        num_list.append(str(random.randint(0, 9)))
    return "".join(num_list)


def generate_random_num(m, n):
    assert isinstance(m, int)
    assert isinstance(n, int)
    selected = []
    i = 0
    while n > 0:
        if random.randint(0, 9999) % n < m:
            selected.append(i)
            m -= 1
        n -= 1
        i += 1
    return selected


def format_time_string(timestamp):
    now = datetime.datetime.now().strftime("%s")
    ts_delta = int(now) - int(timestamp)
    if ts_delta < 60:
        return "刚刚"
    elif 60 <= ts_delta < 3600:
        return "%d分钟前" % int(ts_delta / 60)
    elif 3600 <= ts_delta < 86400:
        return "%d小时前" % int(ts_delta / 3600)
    elif 86400 <= ts_delta < 2678400:
        return "%d天前" % int(ts_delta / 86400)
    elif 2678400 <= ts_delta < 8035200:
        return "%d月前" % int(ts_delta / 2678400)
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
