# -*-coding:utf8-*-
import threading
import time

import bson
from bynamodb import patch_dynamodb_connection
import redis
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.threads import deferToThread

from chat import get_config
from chat.decorators import must_be_in_channel
from chat.dna.protocol import DnaProtocol, ProtocolError
from chat.transmission import Transmitter
from models import User, Message


class ChatProtocol(DnaProtocol):
    def __init__(self):
        self.user = None
        self.status = 'pending'
        self.pending_messages = []
        self.pending_messages_lock = threading.Lock()

    def requestReceived(self, request):
        processor = getattr(self, 'do_%s' % request.method, None)
        if processor is None:
            raise ProtocolError('Unknown method')
        processor(request)

    def do_authenticate(self, request):
        def send_unread_messages(channel, published_at):
            messages = [
                message.to_dict()
                for message in Message.query(channel__eq=channel, published_at__gt=published_at)
            ]

            with self.pending_messages_lock:
                pending_messages = list(self.pending_messages)
                self.pending_messages = []

            for message in pending_messages:
                message = bson.loads(message)
                del message['method']
                messages.append(message)

            self.transport.write(bson.dumps(dict(method=u'unread', messages=messages)))

        def ready_to_receive(result):
            self.status = 'stable'

        self.user = User.query(id__eq=request['token']).next()
        self.factory.channels.setdefault(self.user.channel, []).append(self)
        d = deferToThread(send_unread_messages, self.user.channel, request['last_published_at'])
        d.addCallback(ready_to_receive)

    @must_be_in_channel
    def do_publish(self, request):
        message = dict(
            message=request['message'],
            writer=self.user.id,
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
        Transmitter(self).start()


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