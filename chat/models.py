# -*-coding:utf8-*-
from bynamodb.attributes import StringAttribute, NumberAttribute
from bynamodb.model import Model


class Message(Model):
    channel = StringAttribute(hash_key=True)
    published_at = NumberAttribute(range_key=True)
    user = StringAttribute()
    message = StringAttribute()