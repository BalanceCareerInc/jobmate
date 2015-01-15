# -*-coding:utf8-*-
from collections import namedtuple
from boto import sns
from bynamodb.indexes import GlobalIndex, GlobalAllIndex
from flask import json
from werkzeug.utils import cached_property
from bynamodb.attributes import StringAttribute, NumberAttribute, MapAttribute, SetAttribute, ListAttribute
from bynamodb.model import Model


class CoordinateGroup(namedtuple('CoordinateGroup', ['name', 'default', 'cases'])):
    def __new__(cls, name, default=None, cases=None):
        if cases is None:
            cases = dict()
        elif not isinstance(cases, dict):
            raise TypeError('Children have to be a dict, not "%s"' % type(cases))
        for children in cases.values():
            if not isinstance(children, (tuple, list)):
                raise TypeError('Type of all cases values have to be '
                                'list or tuple, not "%s"' % type(children))
            for child in children:
                if not isinstance(child, cls):
                    raise TypeError('Type of all child of cases value have to be '
                                    'CoordinateGroup, not "%s"' % type(child))
        return super(CoordinateGroup, cls).__new__(cls, name, default, cases)


class Coordinate(Model):
    GROUPS = [
        CoordinateGroup('age'),
        CoordinateGroup('school-type', cases=dict(undergraduate=[
            CoordinateGroup('university'),
            CoordinateGroup('major')
        ])),
        CoordinateGroup('apply-type'),
        CoordinateGroup('orientation'),
        CoordinateGroup('looking-for-now')
    ]
    GROUP_TYPE_CRITERIA = 'looking-for-now', 'orientation'
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
        def group_value_pairs(groups):
            pairs = []
            for group in groups:
                value = user.matching_info[group]
                pairs.append((group, value))
                if value in group.cases:
                    pairs += group_value_pairs(group.cases[value])
            return pairs
        normalizer = CoordinateNormalizer()
        return [
            normalizer.normalize(group, value)
            for group, value in group_value_pairs(cls.GROUPS)
        ]


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
    pair_id = StringAttribute(null=True)
    nickname = StringAttribute()
    phone_number = StringAttribute()
    gender = StringAttribute()
    activated_at = NumberAttribute()

    device_token = StringAttribute(null=True)
    endpoint_arn = StringAttribute(null=True)
    matching_info = MapAttribute()


    @cached_property
    def group_type(self):
        return Coordinate.group_type_of(self)

    @cached_property
    def coordinates(self):
        return Coordinate.of(self)

    @cached_property
    def pair(self):
        if self.pair_id is None:
            return None
        return Pair.get_item(self.pair_id)

    @property
    def channel(self):
        return self.pair_id

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
    user_ids = SetAttribute()
    matched_at = NumberAttribute()
    title = StringAttribute(null=True)
    note_ids = ListAttribute(null=True, default=[])


class Note(Model):
    # It is vulnerable. Because if notes are created frequently by many users, uuid can be guessed by brute forcing.
    # TODO: Make permission checkable
    id = StringAttribute(hash_key=True)
    writer_id = StringAttribute()
    title = StringAttribute()
    content = StringAttribute()
    published_at = NumberAttribute()

    class WriterIndex(GlobalAllIndex):
        read_throughput = 1
        write_throughput = 1

        hash_key = 'writer_id'
        range_key = 'published_at'


class Comment(Model):
    note_id = StringAttribute(hash_key=True)
    published_at = NumberAttribute(range_key=True)
    writer_id = StringAttribute()
    content = StringAttribute()


class DeletedArchive(Model):
    type = StringAttribute(hash_key=True)
    deleted_at = NumberAttribute(range_key=True)
    owner_id = StringAttribute()
    data = StringAttribute()
