# -*-coding:utf8-*-
import time
import uuid
from collections import defaultdict

from web.matching import Matcher
from models import User


def pairing():
    users = User.scan(partner__null=True)
    group_users = defaultdict(list)
    [group_users[user.group_type].append(user)for user in users]
    for group, users in group_users.iteritems():
        pairs = Matcher().match(users)
        for u1, u2 in pairs:
            channel = '%f-%s' % (time.time(), uuid.uuid1())
            u1.partner = u2.id
            u2.partner = u1.id
            u1.channel = channel
            u2.channel = channel
            u1.save()
            u2.save()
