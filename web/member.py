# -*-coding:utf8-*-
from uuid import uuid1
from boto import sns

from flask import Blueprint, request, abort, jsonify, current_app

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
    user = User(
        id=str(uuid1()),
        gender=cleaned_params.pop('gender'),
        device_token=cleaned_params.pop('device_token'),
        matching_info=cleaned_params,
    )
    conn = sns.connect_to_region('ap-northeast-1')
    response = conn.create_platform_endpoint(current_app.config['APP_ARN'], user.device_token, user.id)
    user.endpoint_arn = response['CreatePlatformEndpointResponse']['CreatePlatformEndpointResult']['EndpointArn']
    user.save()
    return jsonify(username=user.id)
