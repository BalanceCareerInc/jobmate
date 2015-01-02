from bynamodb.attributes import StringAttribute, NumberAttribute
from bynamodb.model import Model


class Coordinate(Model):
    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()
