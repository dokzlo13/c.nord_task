import logging

from tornado.tcpserver import TCPServer

from core.marshalling import pack_stats
from core import Supervisor

logger = logging.getLogger(__name__)


class WatcherServer(TCPServer):
    def __init__(self, watchers, sources_statistics, **kwargs):
        super().__init__(**kwargs)
        self.watchers = watchers
        self.online_statistics = sources_statistics
        logger.info("WatcherServer initalized!")

    async def handle_stream(self, stream, address):
        await self.on_connect(stream)
        await stream.read_until_close()
        await self.on_disconnect(stream)

    async def on_connect(self, stream):
        await self.send_online_statistics(stream)
        self.watchers.add(Supervisor(stream))

    async def send_online_statistics(self, stream):
        for stat in self.online_statistics.values():
            await stream.write(pack_stats(stat))

    async def on_disconnect(self, stream):
        self.watchers.remove(Supervisor(stream))
