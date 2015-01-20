# -*-coding:utf8-*-
import numpy
import random
import time

from uuid import uuid1

from boto import sns

from flask import Blueprint, request, abort, jsonify, current_app, session
import redis

from models import Coordinate, User
from .decorators import login_required
from .tasks import save_pair
from .utils.sms import send_sms


bp = Blueprint('member', __name__)


@bp.route('/require-sms/', methods=['GET'])
def send_auth_sms():
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return abort(400)
    phone_number = ''.join([x for x in phone_number.strip() if x in '0123456789'])

    try:
        User.scan(phone_number__eq=phone_number).next()
    except StopIteration:
        session['phone_number'] = phone_number
        session['auth_number'] = str(random.randint(10000, 99999))
    send_sms(phone_number, u'[입사동기]\n인증번호: {0}'.format(session['auth_number']))
    return jsonify(status=True, sid=session.sid)


@bp.route('/auth-sms/', methods=['POST'])
def auth_phone_number():
    user_input_number = request.json.get('auth_number')

    if str(user_input_number) != session['auth_number']:
        return abort(400)

    del session['auth_number']

    redis_session = redis.StrictRedis(current_app.config['REDIS_HOST'])
    key = str(uuid1())
    redis_session.set(key, session['phone_number'])
    redis_session.expire(key, 60 * 60 * 24)
    return jsonify(key=key), 202


@bp.route('/register', methods=['POST'])
def register():
    def clean(params):
        default_keys = list(BASIC_INFO_KEYS) + [group.name for group in Coordinate.GROUPS]
        if not all([key in params for key in default_keys]):
            return None
        return params

    redis_key = request.json['key']
    del request.json['key']
    redis_session = redis.StrictRedis(current_app.config['REDIS_HOST'])
    phone_number = redis_session.get(redis_key)
    redis_session.delete(redis_key)

    BASIC_INFO_KEYS = 'gender', 'nickname', 'device_token'

    cleaned_params = clean(request.json)
    if cleaned_params is None:
        print request.json
        return abort(400)

    basic_info = dict((key, cleaned_params.pop(key)) for key in BASIC_INFO_KEYS)
    user = User(
        id=str(uuid1()),
        phone_number=phone_number,
        matching_info=cleaned_params,
        activated_at=time.time(),
        **basic_info
    )

    conn = sns.connect_to_region('ap-northeast-1')
    response = conn.create_platform_endpoint(current_app.config['APP_ARN'], user.device_token, user.id)
    user.endpoint_arn = response['CreatePlatformEndpointResponse']['CreatePlatformEndpointResult']['EndpointArn']
    user.save()
    return jsonify(id=user.id), 201


@bp.route('/closest', methods=['GET'])
@login_required
def find_closest():
    conditions = dict(
        pair__null=True,
        id__ne=request.user.id,
    )
    if request.user.gender != 'M':
        conditions['gender__eq'] = 'F'
    unmatched_users = User.scan(**conditions)

    closest = (float('inf'), None)
    base_coordinate = request.user.coordinates
    for user in unmatched_users:
        if request.user.group_type != user.group_type:
            continue
        distance = numpy.linalg.norm(base_coordinate-user.coordinates)
        if distance < closest[0]:
            closest = distance, user

    CRITICAL_DISTANCE = 0.1
    if closest < CRITICAL_DISTANCE:
        save_pair(request.user, user)
        return jsonify(matched=True)
    else:
        return jsonify(matched=False)
