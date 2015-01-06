# -*-coding:utf8-*-
import bson
import redis
import time

from threading import Thread

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from chat.decorators import must_be_in_channel

from chat.dna.protocol import DnaProtocol, ProtocolError


class ChatProtocol(DnaProtocol):
    channel = None
    user = None

    def requestReceived(self, request):
        processor = getattr(self, 'do_%s' % request.method, None)
        if processor is None:
            raise ProtocolError('Unknown method')
        processor(request)

    def do_authenticate(self, request):
        self.channel = request['channel']
        self.user = request['user']
        self.factory.channels.setdefault(self.channel, []).append(self)

    @must_be_in_channel
    def do_publish(self, request):
        message = bson.dumps(dict(
            message=request['message'], writer=self.user, published_at=time.time()
        ))
        self.factory.session.publish(self.channel, message)

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
            data = message['data']
            data['method'] = 'publish'
            for client in self.factory.channels[message['channel']]:
                client.transport.write(data)


def run():
    reactor.listenTCP(9338, ChatFactory())
    reactor.run()


if __name__ == '__main__':
    run()