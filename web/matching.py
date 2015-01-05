# -*-coding:utf8-*-
from collections import Counter
import numpy
from sklearn.cluster import AgglomerativeClustering


def pairing(users):
    pairs, unpaired = _pairing_by_agglomerative(users)
    pairs, rejected = _reject_homo(pairs)
    unpaired += rejected

    if len(unpaired) == 0:
        return pairs

    all_females = [user for user in users if user.gender == 'F']
    unpaired_females = [user for user in unpaired if user.gender == 'F']
    if len(unpaired_females)/float(len(all_females)) > 0.95:
        female_pairs = [pair for pair in pairs if pair[0].gender == pair[1].gender == 'F']
        pairs += female_pairs
        [unpaired.remove(user) for pair in female_pairs for user in pair]
        pairs = pairs + _pairing_by_brute(unpaired)
        return pairs

    return pairs + pairing(unpaired)


def _pairing_by_agglomerative(users):
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

    unpaired = [
        result[cluster].pop()
        for cluster, cnt in counter.iteritems() if cnt % 2 == 1
    ]
    pairs = reduce(lambda x, y: x+y, [
        [paired_users] if len(paired_users) == 2
        else list(split(paired_users, 2))
        for paired_users in result.values()
        if len(paired_users) != 0
    ])
    return pairs, unpaired


def _reject_homo(pairs):
    new_pairs = []
    rejected = []
    for pair in pairs:
        if pair[0].gender == pair[1].gender:
            rejected.append(pair[0])
            rejected.append(pair[1])
        else:
            new_pairs.append(pair)
    return new_pairs, rejected


def _pairing_by_brute(users):
    females = [user for user in users if user.gender == 'F']
    pairs = []
    for female in females:
        min_distance = (float('inf'), None)
        if female not in users:
            continue
        for user in users[users.index(female)+1:]:
            distance = numpy.linalg.norm(numpy.array(user.coordinates) - numpy.array(female.coordinates))
            min_distance = min(min_distance, (distance, user))
        users = [user for user in users if user != min_distance[1] and user != female]
        if min_distance[1] is not None:
            pairs.append((female, min_distance[1]))
    return pairs
