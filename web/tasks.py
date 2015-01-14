# -*-coding:utf8-*-
import time
import uuid
from collections import defaultdict

from web.matching import Matcher
from models import User, Pair


def save_pair(pair):
    u1, u2 = pair
    pair = Pair.put_item(
        id=str(uuid.uuid1()),
        user_ids={u1, u2},
        matched_at=time.time()
    )
    u1.pair_id = pair.id
    u2.pair_id = pair.id
    u1.save()
    u2.save()
    u1.push(dict(
        message=u'임시매칭이 되었습니다 확인해보세요!!',
        matched_at=pair.matched_at,
        type='MATCHING'
    ))
    u2.push(dict(
        message=u'임시매칭이 되었습니다 확인해보세요!!',
        matched_at=pair.matched_at,
        type='MATCHING'
    ))


def find_pairs():
    users = User.scan(pair__null=True)
    group_users = defaultdict(list)
    [group_users[user.group_type].append(user) for user in users]
    for group, users in group_users.iteritems():
        pairs = Matcher().find_pairs(users)
        for pair in pairs:
            save_pair(pair)
