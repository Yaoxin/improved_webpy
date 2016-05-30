#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from base.log import logger

__author__ = 'cloudy'

urls = []


class HandleMetaClass(type):
    '''
    meta class for action handle
    '''

    def __new__(cls, name, base, attrs):
        return type.__new__(cls, name, base, attrs)

    def __init__(cls, name, base, attrs):
        logger.debug("Add route: %s" % attrs["url"])
        urls.append(attrs["url"])
        urls.append("%s.%s" % (cls.__module__, name))
        super(HandleMetaClass, cls).__init__(name, base, attrs)
