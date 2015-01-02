from bynamodb.attributes import StringAttribute, NumberAttribute
from bynamodb.model import Model


class Coordinate(Model):

    __fixtures__ = 'universities.json',

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()
