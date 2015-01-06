import os

from flask import Flask
from flask.ext.compress import Compress

from bynamodb import patch_dynamodb_connection
from web.session import RedisSessionInterface


def create_app(config_file='baseconfig.py'):
    app = Flask(__name__)
    config_file = os.path.join(os.getcwd(), 'conf', config_file)
    app.config.from_pyfile(config_file)
    Compress(app)
    patch_dynamodb_connection(
        host=app.config['DYNAMODB_HOST'],
        port=app.config['DYNAMODB_PORT'],
        is_secure=app.config['DYNAMODB_IS_SECURE'],
    )
    app.session_interface = RedisSessionInterface(app.config['REDIS_HOST'])
    return app
