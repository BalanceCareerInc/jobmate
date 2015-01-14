# -*-coding:utf8-*-
import datetime
import numpy
import random
from uuid import uuid1

from boto import sns

from flask import Blueprint, request, abort, jsonify, current_app, session

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
    print session
    print request.headers
    return jsonify(status=True)


@bp.route('/auth-sms/', methods=['POST'])
def auth_phone_number():
    user_input_number = request.json.get('auth_number')
    print session
    print request.headers

    if user_input_number != session['auth_number']:
        return abort(400)

    del session['auth_number']

    user = User.put_item(
        id=str(uuid1()),
        phone_number=session['phone_number'],
        activated_at=str(datetime.datetime.now())
    )
    return jsonify(id=user.id)


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
    return jsonify(id=user.id)


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
