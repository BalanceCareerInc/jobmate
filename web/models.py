from bynamodb.attributes import StringAttribute, NumberAttribute, ListAttribute
from bynamodb.model import Model


class Coordinate(Model):

    __fixtures__ = 'university', 'recruit_exp'
    GROUPS = __fixtures__

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()


class User(Model):
    username = StringAttribute(hash_key=True)
    university = StringAttribute()
    recruit_exp = NumberAttribute()
    coordinates = ListAttribute()