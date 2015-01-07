# -*-coding:utf8-*-
import bson
from bynamodb import patch_dynamodb_connection
import redis
import time

from threading import Thread

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from chat.decorators import must_be_in_channel

from chat.dna.protocol import DnaProtocol, ProtocolError
from models import User


class ChatProtocol(DnaProtocol):
    channel = None
    user = None

    def requestReceived(self, request):
        processor = getattr(self, 'do_%s' % request.method, None)
        if processor is None:
            raise ProtocolError('Unknown method')
        processor(request)

    def do_authenticate(self, request):
        self.user = request['user']
        user = User.query(username__eq=self.user).next()
        self.channel = user.channel
        self.factory.channels.setdefault(self.channel, []).append(self)

    @must_be_in_channel
    def do_publish(self, request):
        message = dict(
            message=request['message'],
            writer=self.user,
            published_at=time.time(),
            method=u'publish'
        )
        message = bson.dumps(message)
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
            for client in self.factory.channels[message['channel']]:
                client.transport.write(message['data'])


def run(config_file='localconfig'):
    with open('../conf/%s' % config_file, 'r') as f:
        data = f.read()
    config = dict()
    default = dict()
    exec '' in default
    exec data in config
    config = dict((k, v) for k, v in config.iteritems() if k not in default)
    patch_dynamodb_connection(
        host=config['DYNAMODB_HOST'],
        port=config['DYNAMODB_PORT'],
        is_secure=config['DYNAMODB_IS_SECURE']
    )
    reactor.listenTCP(9339, ChatFactory(config['REDIS_HOST']))
    reactor.run()


if __name__ == '__main__':
    run('localconfig.py')