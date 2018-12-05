from dataclasses import dataclass, field
from typing import List

SOURCE_STATUSES = {1: "IDLE", 2: "ACTIVE", 3: "RECHARGE"}
REVERSE_SOURCE_STATUSES = {v: k for k, v in SOURCE_STATUSES.items()}

OUT_MSG_FAIL = 0x12
OUT_MSG_SUCCEED = 0x11
OUT_MSG_EMPTY = 0x0

@dataclass
class InboxMessage:
    header: int = field(default=0)
    message_number: int = field(default=0)
    source_name: str = field(default='')
    source_status: str = field(default='')
    fields_count: int = field(default=0)
    fields: List[tuple] = field(default_factory=lambda :[()])
    source_xor: int = field(default=0)

    raw_payload: bytes = field(default=b'', repr=False)
    broken_message: bool = field(default=False, repr=False)


@dataclass
class OutboxMessage:
    header: int
    message_number: int


@dataclass
class SourceStatistics:
    name: str
    status: str
    last_message_number: int
    last_message_timestamp_in_ms: int
