# -*-coding:utf8-*-
import random
from uuid import uuid1
import datetime

from flask import Blueprint, request, abort, jsonify, session

from models import Coordinate, User
from web.utils.sms import send_sms


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
        default_keys = ['gender'] + list(Coordinate.DEFAULT_GROUPS)
        if not all([key in params for key in default_keys]):
            return None
        params.update(looking_for_now=True, orientation='etc')
        return params

    cleaned_params = clean(request.json)
    if cleaned_params is None:
        return abort(400)
    user = User.put_item(
        id=str(uuid1()),
        gender=cleaned_params.pop('gender'),
        matching_info=cleaned_params,
    )
    return jsonify(id=user.id)
