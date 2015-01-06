# -*-coding:utf8-*-
from threading import Thread

import redis
from twisted.internet import reactor
from twisted.internet.protocol import Factory

from chat.dna.protocol import DnaProtocol, ProtocolError


class ChatProtocol(DnaProtocol):
    channel = None

    def requestReceived(self, request):
        if self.channel is None:
            if request.method != 'joinChannel':
                raise ProtocolError('Must join in the channel')
            self.channel = request['channel']
            self.factory.channels.setdefault(self.channel, []).append(self)
        else:
            self.factory.session.publish(self.channel, request['message'])

    def connectionLost(self, reason=None):
        print reason
        if self.channel is not None:
            self.factory.channels[self.channel].remove(self)


class ChatFactory(Factory):
    protocol = ChatProtocol
    channels = dict()

    def __init__(self, redis_host='localhost'):
        self.session = redis.StrictRedis(host=redis_host)
        RedisSubscriber(self).start()


class RedisSubscriber(Thread):
    def __init__(self, factory):
        Thread.__init__(self)
        self.factory = factory

    def run(self):
        pubsub = self.factory.session.pubsub()
        pubsub.psubscribe('*')
        pubsub.listen().next()
        for message in pubsub.listen():
            for client in self.factory.channels[message['channel']]:
                client.transport.write(message['data'])


def run():
    reactor.listenTCP(9338, ChatFactory())
    reactor.run()


if __name__ == '__main__':
    run()