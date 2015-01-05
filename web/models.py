# -*-coding:utf8-*-
from werkzeug.utils import cached_property
from bynamodb.attributes import StringAttribute, NumberAttribute, MapAttribute
from bynamodb.model import Model


class Coordinate(Model):
    DEFAULT_GROUPS = 'university', 'age'
    GROUP_NAMES = 'FUTURE_ETC', 'NOW_ETC'
    GROUP_WEIGHT = dict(
        university=10,
        recruit_exp=10,
        goal_companies=9,
        age=5
    )
    __fixtures__ = 'university', 'recruit_exp', 'goal_companies'

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()

    @classmethod
    def of(cls, user):
        groups = list(Coordinate.DEFAULT_GROUPS) + \
            getattr(cls, '_groups_of_%s' % user.group_name)(user)
        normalizer = CoordinateNormalizer()
        return [
            value
            for group in groups
            for value in normalizer.normalize(group, user.matching_info[group])
        ]

    @classmethod
    def _groups_of_FUTURE_ETC(cls, user):
        return []

    @classmethod
    def _groups_of_NOW_ETC(cls, user):
        return ['recruit_exp', 'goal_companies']


class CoordinateNormalizer(object):
    def normalize(self, group, value):
        normalizer = getattr(self, '_normalize_%s' % group, None)
        if not normalizer:
            return [Coordinate.get_item(value).value]
        return normalizer(value) * Coordinate.GROUP_WEIGHT[group]

    @staticmethod
    def _normalize_recruit_exp(value):
        return [Coordinate.get_item(u'공채%d회' % min(value, 2)).value]

    @staticmethod
    def _normalize_goal_companies(value):
        value = reduce(
            lambda x, y: x+y,
            [[company] * (3-i) for i, company in enumerate(value)]
        )
        companies = sorted([
            company.name
            for company in Coordinate.scan(group__eq='goal_companies')
        ])
        return [value.count(company) for company in companies]

    @staticmethod
    def _normalize_age(value):
        return [(value - 20)]


class User(Model):
    username = StringAttribute(hash_key=True)
    gender = StringAttribute()
    group_name = StringAttribute()
    matching_info = MapAttribute()

    @cached_property
    def coordinates(self):
        return Coordinate.of(self)

    def __repr__(self):
        def printable(x):
            if type(x) in (tuple, list):
                x = ','.join(x)
            return unicode(x).encode('utf8')

        return '<User: %s/%s/%s>' % (
            self.username.encode('utf8'),
            self.gender,
            '/'.join([
                '%s: %s' % (printable(k), printable(v))
                for k, v in self.matching_info.iteritems()
            ])
        )