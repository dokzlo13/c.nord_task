import logging

from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer

from core.marshalling import pack_outbox, unpack_inbox
from core.validators import validate_inbox
from core.types import OutboxMessage, SourceStatistics
from core.types import OUT_MSG_FAIL, OUT_MSG_SUCCEED, OUT_MSG_EMPTY
from core.utils import now

logger = logging.getLogger(__name__)


class MessageServer(TCPServer):
    def __init__(self, watchers, sources_statistics, **kwargs):
        super().__init__(**kwargs)
        self.watchers = watchers
        self.sources_statistics = sources_statistics
        logger.info("MessageServer initalized!")

    async def handle_stream(self, stream, address):
        while True:
            try:
                await self._handle_single_message(stream)
            except StreamClosedError:
                break

    async def _handle_single_message(self, stream):
        inbox_message = await unpack_inbox(stream)
        try:
            validate_inbox(inbox_message)
        except Exception as e:
            logger.warning("During message processing exception \"{0}\" catched".format(e.__class__.__name__))
            outbox_message = OutboxMessage(OUT_MSG_FAIL, OUT_MSG_EMPTY)
        else:
            outbox_message = OutboxMessage(OUT_MSG_SUCCEED, inbox_message.message_number)
            await self.on_valid_message(inbox_message)

        await stream.write(pack_outbox(outbox_message))

    async def on_valid_message(self, message):
        self.sources_statistics[message.source_name] = SourceStatistics(
            message.source_name,
            message.source_status,
            message.message_number,
            now(),
        )
        for observer in self.watchers:
            await observer.notify(message)
