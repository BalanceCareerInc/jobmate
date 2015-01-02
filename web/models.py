# -*-coding:utf8-*-
from bynamodb.attributes import StringAttribute, NumberAttribute
from bynamodb.model import Model


class Coordinate(Model):
    GROUPS = 'university', 'recruit_exp'
    __fixtures__ = GROUPS

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()

    @classmethod
    def normalize(cls, group, value):
        normalizer = getattr(cls, '_normalize_%s' % group, None)
        if not normalizer:
            return value
        return normalizer(value)

    @classmethod
    def _normalize_recruit_exp(cls, value):
        return u'공채%d회' % min(value, 2)


class User(Model):
    username = StringAttribute(hash_key=True)
    university = StringAttribute()
    recruit_exp = NumberAttribute()

    @property
    def coordinates(self):
        return [
            Coordinate.get_item(Coordinate.normalize(group, getattr(self, group))).value
            for group in Coordinate.GROUPS
        ]

    def __repr__(self):
        return '<User: %s/%s>' % (
            self.username.encode('utf8'),
            '/'.join([
                unicode(getattr(self, group)).encode('utf8')
                for group in Coordinate.GROUPS
            ])
        )