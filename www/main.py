#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import web
from base import *
from config import configs
from url import urls

modules = ['apps.test']


def add_modules(module_list=None):
    for mod in module_list:
        load_module(mod)


# init db:
create_engine(configs.db.user, configs.db.passwd, configs.db.database)

# add modules
add_modules(modules)

# init wsgi app:
app = web.application(urls, globals(), autoreload=False)
web.config.debug = False

if __name__ == '__main__':
    app.run()
else:
    application = app.wsgifunc()
