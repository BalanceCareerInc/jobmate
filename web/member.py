# -*-coding:utf8-*-
from uuid import uuid1
from boto import sns

from flask import Blueprint, request, abort, jsonify, current_app

from models import Coordinate, User


bp = Blueprint('member', __name__)


@bp.route('/register', methods=['POST'])
def register():
    def clean(params):
        default_keys = BASIC_INFO_KEYS + Coordinate.DEFAULT_GROUPS
        if not all([key in params for key in default_keys]):
            return None
        params.update(looking_for_now=True, orientation='etc')
        return params

    BASIC_INFO_KEYS = 'gender', 'nickname', 'device_token'

    cleaned_params = clean(request.json)
    if cleaned_params is None:
        return abort(400)

    basic_info = dict((key, cleaned_params.pop(key)) for key in BASIC_INFO_KEYS)
    user = User(
        id=str(uuid1()),
        matching_info=cleaned_params,
        **basic_info
    )
    conn = sns.connect_to_region('ap-northeast-1')
    response = conn.create_platform_endpoint(current_app.config['APP_ARN'], user.device_token, user.id)
    user.endpoint_arn = response['CreatePlatformEndpointResponse']['CreatePlatformEndpointResult']['EndpointArn']
    user.save()
    return jsonify(username=user.id)
