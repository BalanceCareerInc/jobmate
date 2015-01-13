# -*-coding:utf8-*-
import time
import uuid
from collections import defaultdict

from web.matching import Matcher
from models import User


def pairing():
    def make_pair(user_, partner):
        user_.partner = partner.username
        user_.channel = channel
        user_.matched_at = now
        user_.save()

    users = User.scan(partner__null=True)
    group_users = defaultdict(list)
    [group_users[user.group_type].append(user) for user in users]
    for group, users in group_users.iteritems():
        pairs = Matcher().match(users)
        for u1, u2 in pairs:
            now = time.time()
            channel = '%f-%s' % (now, uuid.uuid1())
            make_pair(u1, u2)
            make_pair(u2, u1)
