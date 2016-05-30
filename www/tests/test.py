#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = 'cloudy'

from base import *
import urllib2, urllib
import json
import requests

client = APIClient.Instance()

if __name__ == '__main__':
    print client.user.get.post(user_id=3456)




