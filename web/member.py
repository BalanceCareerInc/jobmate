# -*-coding:utf8-*-
from uuid import uuid1

from flask import Blueprint, request, abort, jsonify

from models import Coordinate, User


bp = Blueprint('member', __name__)


@bp.route('/register', methods=['POST'])
def register():
    def clean(params):
        default_keys = ['gender'] + list(Coordinate.DEFAULT_GROUPS)
        if not all([key in params for key in default_keys]):
            return None
        params.update(looking_for_now=True, orientation='etc')
        return params
    cleaned_params = clean(request.json)
    if cleaned_params is None:
        return abort(400)
    user = User.put_item(
        username=str(uuid1()),
        gender=cleaned_params.pop('gender'),
        matching_info=cleaned_params,
    )
    return jsonify(username=user.username)
