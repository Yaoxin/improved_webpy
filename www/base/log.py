#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = 'cloudy'

import logging

logger = logging.getLogger()

handle = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
handle.setFormatter(formatter)

logger.addHandler(handle)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger.debug("hello world")
    logger.info("hello woRrld")

