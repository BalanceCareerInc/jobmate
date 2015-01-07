# -*-coding:utf8-*-
from uuid import uuid1
from flask import Blueprint, request, abort
from web.models import Coordinate, User

bp = Blueprint('member', __name__)


@bp.route('/register', methods=['POST'])
def register():
    def clean(params):
        default_keys = ['gender'] + list(Coordinate.DEFAULT_GROUPS)
        if not all([key in params for key in default_keys]):
            return None
        return params
    cleaned_params = clean(request.json)
    if cleaned_params is None:
        return abort(400)
    user = User.put_item(
        username=uuid1(),
        matching_info=cleaned_params
    )
    return user.username
