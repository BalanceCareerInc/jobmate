# -*-coding:utf8-*-
from collections import Counter
import numpy
from sklearn.cluster import AgglomerativeClustering


def pairing(users):
    def split(l, n):
        for x in xrange(0, len(l), n):
            yield l[x:x+n]

    algorithm = AgglomerativeClustering(n_clusters=len(users)/2, n_components=2)
    algorithm.fit([user.coordinates for user in users])

    result = dict()
    counter = Counter()
    for i, cluster in enumerate(algorithm.labels_):
        counter[cluster] += 1
        result.setdefault(cluster, []).append(users[i])

    unpaired = numpy.array([
        result[cluster].pop()
        for cluster, cnt in counter.iteritems() if cnt % 2 == 1
    ])
    result = reduce(lambda x, y: x+y, [
        [users] if len(users) == 2
        else list(split(users, 2))
        for users in result.values()
        if len(users) != 0
    ])

    if len(unpaired) == 0:
        return result

    return result + pairing(unpaired)

