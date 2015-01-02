# -*-coding:utf8-*-
import os
import pytest
import shutil
import subprocess

from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table

from manage import init_db
from web.app import create_app


process = None
my_app = create_app('testconfig.py')


@pytest.fixture
def app(tmpdir):
    my_app.config['UPLOAD_FOLDER'] = str(tmpdir)
    return my_app


def pytest_configure():
    global process
    if 'TESTING_PATH' in my_app.config:
        os.chdir(my_app.config['TESTING_PATH'])
    shutil.rmtree('dynamodb/testdb', True)
    os.mkdir('dynamodb/testdb')
    dev_null = open(os.devnull, 'wb')
    process = subprocess.Popen([
        '/usr/bin/java', '-Djava.net.preferIPv4Stack=true',
        '-Djava.library.path=./dynamodb/DynamoDBLocal_lib', '-jar',
        'dynamodb/DynamoDBLocal.jar', '-port', '8001',
        '-dbPath', './dynamodb/testdb'
    ], stdout=dev_null, stderr=dev_null)


def pytest_unconfigure():
    process.terminate()


def pytest_runtest_setup():
    init_db()


def pytest_runtest_teardown():
    table_names = DynamoDBConnection().list_tables()['TableNames']
    for table_name in table_names:
        Table(table_name).delete()
