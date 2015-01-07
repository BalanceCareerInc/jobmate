# -*-coding:utf8-*-
import bson
from bynamodb import patch_dynamodb_connection
import redis
import time

from threading import Thread

from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.threads import deferToThread
from chat import get_config
from chat.decorators import must_be_in_channel

from chat.dna.protocol import DnaProtocol, ProtocolError
from models import User, Message


class ChatProtocol(DnaProtocol):
    user = None

    def requestReceived(self, request):
        processor = getattr(self, 'do_%s' % request.method, None)
        if processor is None:
            raise ProtocolError('Unknown method')
        processor(request)

    def do_authenticate(self, request):
        def send_unread_messages(channel, published_at):
            messages = Message.query(channel__eq=channel, published_at__gt=published_at)
            messages = [dict(
                writer=message.user,
                published_at=float(message.published_at),
                message=message.message
            ) for message in messages]
            self.transport.write(bson.dumps(dict(method=u'unread', messages=messages)))

        def connect_to_channel(result):
            self.factory.channels.setdefault(self.user.channel, []).append(self)

        self.user = User.query(username__eq=request['user']).next()
        d = deferToThread(send_unread_messages, self.user.channel, request['last_published_at'])
        d.addCallback(connect_to_channel)

    @must_be_in_channel
    def do_publish(self, request):
        message = dict(
            message=request['message'],
            writer=self.user.username,
            published_at=time.time(),
            method=u'publish'
        )
        message = bson.dumps(message)
        self.factory.session.publish(self.user.channel, message)

    def connectionLost(self, reason=None):
        print reason
        if self.user and self.user.channel:
            self.factory.channels[self.user.channel].remove(self)


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
    config = get_config(config_file)
    patch_dynamodb_connection(
        host=config['DYNAMODB_HOST'],
        port=config['DYNAMODB_PORT'],
        is_secure=config['DYNAMODB_IS_SECURE']
    )
    reactor.listenTCP(9339, ChatFactory(config['REDIS_HOST']))
    reactor.run()


if __name__ == '__main__':
    run('localconfig.py')