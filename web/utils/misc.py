# -*-coding:utf8-*-
from boto.dynamodb.types import convert_num
from decimal import Decimal
from bynamodb.model import Model


def jsonable(item):
    def jsonable_value(value):
        if isinstance(value, Decimal):
            return convert_num(str(value))
        elif isinstance(value, set):
            return list(value)
        else:
            return value

    if hasattr(item, 'items') and callable(item.items):
        return dict((key, jsonable(value)) for key, value in item.items())
    elif isinstance(item, Model):
        return dict(
            (key, jsonable(getattr(item, key)))
            for key in item._get_attributes().keys()
        )
    elif isinstance(item, (tuple, list)):
        return [jsonable(value) for value in item]
    else:
        return jsonable_value(item)
