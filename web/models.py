from bynamodb.attributes import StringAttribute, NumberAttribute, ListAttribute
from bynamodb.model import Model


class Coordinate(Model):

    __fixtures__ = 'university', 'recruit_exp'

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()


class User(Model):
    username = StringAttribute(hash_key=True)
    coordinates = ListAttribute()