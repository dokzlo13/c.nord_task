import functools
import socket

from tornado.iostream import IOStream
from tornado.testing import bind_unused_port, AsyncTestCase, gen_test

from core.marshalling import pack_inbox
from core.types import InboxMessage
from handlers import MessageServer, WatcherServer


class BaseTestCase(AsyncTestCase):
    def setUp(self):
        super().setUp()
        watchers = set()
        sources_statistics = dict()
        self.message_server = MessageServerTestServer(
            watchers=watchers, sources_statistics=sources_statistics
        )
        self.watcher_server = WatcherServerTestServer(
            watchers=watchers, sources_statistics=sources_statistics
        )

    async def connect_messenger(self):
        return await self.message_server.connect()

    async def connect_observer(self):
        return await self.watcher_server.connect()

    def close_fixtures(self):
        self.message_server.close()
        self.watcher_server.close()


class BaseTestServer:
    server_factory = NotImplemented
    client_factory = IOStream

    def __init__(self, **kwargs):
        self.server = self.server_factory(**kwargs)
        sock, self.port = bind_unused_port()
        self.server.add_socket(sock)
        self.clients = []

    async def connect(self):
        client = self.client_factory(socket.socket())
        await client.connect(("localhost", self.port))
        self.clients.append(client)
        return client

    def close(self):
        for client in self.clients:
            client.close()
        self.server.stop()


class MessageServerIOStream(IOStream):
    async def send_message(self, message_number, source_name, source_status, fields):
        message = pack_inbox(
            InboxMessage(
                1, message_number, source_name, source_status, len(fields), fields
            )
        )
        return await self.write(message)


class MessageServerTestServer(BaseTestServer):
    server_factory = MessageServer
    client_factory = MessageServerIOStream


class WatcherServerTestServer(BaseTestServer):
    server_factory = WatcherServer


def safe_gen_test(f):
    return gen_test(closing_gen(f))


def closing_gen(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        try:
            yield from f(self, *args, **kwargs)
        finally:
            self.close_fixtures()
    return wrapper
