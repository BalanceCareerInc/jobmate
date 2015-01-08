#-*-coding:utf8-*-

import httplib
import urllib
from flask import current_app


def send_sms(phone_number, sms_message, sms_callback='07081195567'):
    phone_number = phone_number.replace('-', '')
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'charset': 'UTF-8',
        'x-waple-authorization': 'MTUzNy0xNDAxNzYwNzM2Njk5LTMwNDBiZmFjLTgwNTctNDY5Yy04MGJmLWFjODA1NzM2OWNhOA=='
    }
    request_params = urllib.urlencode({
        'send_phone': sms_callback,
        'dest_phone': phone_number,
        'msg_body': sms_message.encode('utf8')
    })
    url = '/ppurio/{apiVersion}/message/{message_type}/{client_id}'.format(**{
        'apiVersion': '1',
        'message_type': 'sms', #sms로 보내면 lms일 시 알아서 변환해줌
        'client_id': 'studysearch'
    })
    if current_app.config.get('TESTING', False):
        return
    for x in xrange(5):
        try:
            conn = httplib.HTTPConnection('api.openapi.io')
            conn.request('POST', url, request_params, headers)
            conn.getresponse()
        except Exception:
            pass
        else:
            break
