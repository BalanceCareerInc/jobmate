# -*-coding:utf8-*-
from bynamodb.attributes import StringAttribute, NumberAttribute, StringSetAttribute, ListAttribute
from bynamodb.model import Model


class Coordinate(Model):
    GROUPS = dict(
        university=10,
        recruit_exp=10,
        goal_companies=9
    )
    __fixtures__ = GROUPS

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()

    @classmethod
    def normalize(cls, group, value):
        normalizer = getattr(cls, '_normalize_%s' % group, None)
        if not normalizer:
            return [cls.get_item(value).value]
        return normalizer(value) * cls.GROUPS[group]

    @classmethod
    def _normalize_recruit_exp(cls, value):
        return [cls.get_item(u'공채%d회' % min(value, 2)).value]

    @classmethod
    def _normalize_goal_companies(cls, value):
        value = reduce(
            lambda x, y: x+y,
            [[company] * (3-i) for i, company in enumerate(value)]
        )
        companies = sorted([company.name for company in cls.scan(group__eq='goal_companies')])
        return [value.count(company) for company in companies]


class User(Model):
    username = StringAttribute(hash_key=True)
    university = StringAttribute()
    recruit_exp = NumberAttribute()
    goal_companies = ListAttribute()

    @property
    def coordinates(self):
        return [
            value
            for group in Coordinate.GROUPS.keys()
            for value in Coordinate.normalize(group, getattr(self, group))
        ]

    def __repr__(self):
        def printable(x):
            if type(x) in (tuple, list):
                x = ','.join(x)
            return unicode(x).encode('utf8')

        return '<User: %s/%s>' % (
            self.username.encode('utf8'),
            '/'.join([printable(getattr(self, group))for group in Coordinate.GROUPS.keys()])
        )