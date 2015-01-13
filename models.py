# -*-coding:utf8-*-
from boto import sns
from flask import json
from werkzeug.utils import cached_property
from bynamodb.attributes import StringAttribute, NumberAttribute, MapAttribute, SetAttribute, ListAttribute
from bynamodb.model import Model


class Coordinate(Model):
    DEFAULT_GROUPS = 'university', 'age'
    GROUP_TYPE_CRITERIA = 'looking_for_now', 'orientation'
    GROUP_WEIGHT = dict(
        university=10,
        recruit_exp=10,
        goal_companies=9,
        age=2
    )
    __fixtures__ = 'university', 'recruit_exp', 'goal_companies'

    name = StringAttribute(hash_key=True)
    group = StringAttribute()
    value = NumberAttribute()

    @classmethod
    def group_type_of(cls, user):
        criteria = (user.matching_info.get(group) for group in cls.GROUP_TYPE_CRITERIA)
        return tuple(criterion for criterion in criteria if criterion)

    @classmethod
    def of(cls, user):
        group_type_name = {
            (True, 'etc'): 'now_etc',
            (False, 'etc'): 'future_etc'
        }[user.group_type]
        groups = list(Coordinate.DEFAULT_GROUPS) + \
            getattr(cls, '_groups_of_%s' % group_type_name)(user)
        normalizer = CoordinateNormalizer()
        return [
            value
            for group in groups
            for value in normalizer.normalize(group, user.matching_info[group])
        ]

    @classmethod
    def _groups_of_future_etc(cls, user):
        return []

    @classmethod
    def _groups_of_now_etc(cls, user):
        return []
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
            lambda x, y: x + y,
            [[company] * (3 - i) for i, company in enumerate(value)]
        )
        companies = sorted([
            company.name
            for company in Coordinate.scan(group__eq='goal_companies')
        ])
        return [value.count(company) for company in companies]

    @staticmethod
    def _normalize_age(value):
        value = int(value)
        value -= 20
        if value < 4:
            value -= 2
        return [value]


class User(Model):
    id = StringAttribute(hash_key=True)
    pair = StringAttribute(null=True)
    nickname = StringAttribute()

    device_token = StringAttribute(null=True)
    endpoint_arn = StringAttribute(null=True)
    gender = StringAttribute()
    matching_info = MapAttribute()

    @cached_property
    def group_type(self):
        return Coordinate.group_type_of(self)

    @cached_property
    def coordinates(self):
        return Coordinate.of(self)

    @property
    def channel(self):
        return self.pair

    def push(self, data):
        if not self.endpoint_arn:
            raise AttributeError('Attribute endpoint_arn is not set')
        conn = sns.connect_to_region('ap-northeast-1')
        gcm_json = json.dumps(dict(data=data), ensure_ascii=False)
        data = dict(default='default message', GCM=gcm_json)
        conn.publish(
            message=json.dumps(data, ensure_ascii=False),
            target_arn=self.endpoint_arn,
            message_structure='json'
        )

    def __repr__(self):
        def printable(x):
            if type(x) in (tuple, list):
                x = ','.join(x)
            elif type(x) is unicode:
                x = x.encode('utf8')
            return str(x)

        return '<User: %s/%s/%s>' % (
            printable(self.id),
            printable(self.gender),
            '/'.join([
                '%s: %s' % (printable(k), printable(v))
                for k, v in self.matching_info.iteritems()
            ])
        )


class Pair(Model):
    id = StringAttribute(hash_key=True)
    users = SetAttribute()
    matched_at = NumberAttribute()
    title = StringAttribute(null=True)
    notes = ListAttribute(null=True)


class Note(Model):
    writer = StringAttribute(hash_key=True)
    published_at = NumberAttribute(range_key=True)
    title = StringAttribute()
    content = StringAttribute()
