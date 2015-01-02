from flask import Flask
from flask.ext.compress import Compress


def create_app(config_file='baseconfig.py'):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)
    Compress(app)
    return app
