__author__ = 'cloudy'

import os, re
from datetime import datetime

from fabric.api import *

env.user = "root"
env.sudo_user = "root"
env.hosts = ["xxx.xxx.xxx.xxx"]
env.key_filename = "~/.ssh/id_rsa"

db_user = 'root'
db_password = 'xxxxxx'

_TAR_FILE = "www.tar.gz"


def _current_path():
    return os.path.abspath('.')


def _now():
    return datetime.now().strftime('%y-%m-%d_%H.%M.%S')


def backup():
    '''
    dump database on server and backup to local
    '''
    dt = _now()
    f = 'backup-www-%s.sql' % dt
    with cd('/tmp'):
        run('mysqldump --user=%s --password=%s --skip-opt --add-drop-table --default-character-set=utf8 '
            '--a xuanyanyuan > %s' % (db_user, db_password, f))
        run('tar -czvf %s.tar.gz %s' % (f, f))
        get('%s.tar.gz' % f, '%s/backup/' % _current_path())
        run('rm -f %s' % f)
        run('rm -f %s.tar.gz' % f)


def build():
    '''
    build dist package
    '''

    includes = ['apps', 'base', 'core', '*.py']
    excludes = ['tests/*', '*.pyc', '*.pyo']
    local('rm -f dist/%s' % _TAR_FILE)
    print os.path.join(_current_path(), 'www')
    with lcd(os.path.join(_current_path(), 'www')):
        cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        print cmd
        local(' '.join(cmd))


_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/usr/local/www'


def upload():
    '''
    deploy to the server
    '''
    newdir = 'www-%s' % _now()
    run('rm -f %s' % _REMOTE_TMP_TAR)
    put('dist/%s' % _TAR_FILE, _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        sudo('mkdir %s' % newdir)
    with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        sudo('tar -xzvf %s' % _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        sudo('rm -f www')
        sudo('ln -s %s www' % newdir)
    with settings(warn_only=True):
        sudo('/usr/local/python27/bin/supervisorctl stop www')
        sudo('/usr/local/python27/bin/supervisorctl start www')


def rollback():
    '''
    rollback to previous version
    '''
    pass


def deploy():
    execute(build)
    execute(upload)
