# coding:utf-8
__author__ = 'cloudy'

from url import HandleMetaClass
from core.apis import *
from models import User


class PCodeCheckHandle(object):
    __metaclass__ = HandleMetaClass

    url = "/api/user/get"

    @api
    def POST(self):
        i = input_data(user_id='')
        return User.find_first("where id=?", i.user_id)