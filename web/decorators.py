from functools import wraps
from bynamodb.exceptions import ItemNotFoundException
from flask import request, abort, g, session
from werkzeug.local import LocalProxy
from models import User


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            g.user = User.get_item(session['id'])
        except ItemNotFoundException:
            return abort(403)
        request.user = LocalProxy(lambda: g.user)
        return func(*args, **kwargs)
    return wrapper
