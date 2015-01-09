import os

import member

from flask import Flask, request
from flask.ext.compress import Compress

from bynamodb import patch_dynamodb_connection
from web import admin
from web.session import RedisSessionInterface


def create_app(config_file='baseconfig.py'):
    app = Flask(__name__)
    app.config.from_pyfile(os.path.join(os.getcwd(), 'conf', config_file))

    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(member.bp, url_prefix='/member')

    Compress(app)

    patch_dynamodb_connection(
        host=app.config['DYNAMODB_HOST'],
        port=app.config['DYNAMODB_PORT'],
        is_secure=app.config['DYNAMODB_IS_SECURE'],
    )

    app.session_interface = RedisSessionInterface(app.config['REDIS_HOST'])

    @app.after_request
    def allow_access_control(response):
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'content-type,token'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE'
        return response

    return app
