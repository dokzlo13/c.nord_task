from core.marshalling import pack_inbox_fields
from core.types import InboxMessage


class Supervisor:
    def __init__(self, stream):
        self.stream = stream

    def __hash__(self):
        return hash(self.stream)

    def __eq__(self, other):
        return self.stream == other.stream

    async def notify(self, message: InboxMessage):
        return await self.on_message(message)

    async def on_message(self, message: InboxMessage):
        for row in pack_inbox_fields(message):
            await self.stream.write(row)
