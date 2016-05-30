# coding:utf-8
__author__ = 'cloudy'

from base import *


class User(Model):
    __table__ = 'user'

    id = IntegerField(primary_key=True, autoable=True)
    user_id = IntegerField(normal_key=True)
    name = StringField(ddl='varchar(64)')
    age = IntegerField()
    sex = IntegerField(ddl='tinyint(1)')
    introduce = StringField(ddl="varchar(128)")
    status = IntegerField(ddl='tinyint(1)')
    create_time = IntegerField()
    update_time = IntegerField()

    def pre_insert(self):
        self.create_time = int(time.time())

    def pre_update(self):
        self.update_time = int(time.time())
