
import struct
from typing import Iterable

from core.types import InboxMessage, SourceStatistics, OutboxMessage
from core.types import SOURCE_STATUSES, REVERSE_SOURCE_STATUSES
from core.utils import *

def chunked_fields(l):
    r"""
    >>> chunked_fields([b'\x00\x00\x00hello', b'1'])
    [('hello', b'1')]
    """
    chunks = []
    for i in range(0, len(l), 2):
        k, v = l[i:i + 2]
        k = btos(k)
        chunks.append((k, v))
    return chunks

def flaten_fields(l):
    r"""
    >>> flaten_fields([('hello', 1)])
    [b'\x00\x00\x00hello', 1]
    """
    flat = []
    for k, v in l:
        flat.append(stob(k, 8))
        flat.append(v)
    return flat


def _generate_sync_mask(fields_total, with_checksum=True):
    """
    >>> _generate_sync_mask(1)
    '>BH8sBB8sIB'
    >>> _generate_sync_mask(2)
    '>BH8sBB8sI8sIB'
    >>> _generate_sync_mask(2, with_checksum=False)
    '>BH8sBB8sI8sI'
    """
    mask = ">BH8sBB"
    for _ in range(fields_total):
        mask += "8sI"
    if with_checksum:
        mask += "B"
    return mask


async def unpack_inbox(stream):
    header_bytes = await stream.read_bytes(1)
    message_number_bytes = await stream.read_bytes(2)
    source_name_bytes = await stream.read_bytes(8)
    source_status_bytes = await stream.read_bytes(1)
    fields_count = await stream.read_bytes(1)
    fields_count_int = fields_count[0]
    fields_bytes = await stream.read_bytes(fields_count_int * 12)
    source_xor_bytes = await stream.read_bytes(1)

    try:
        header = struct.unpack(">B", header_bytes)[0]
        message_number = struct.unpack(">H", message_number_bytes)[0]
        source_name = btos(struct.unpack(">8s", source_name_bytes)[0])
        source_status = struct.unpack(">B", source_status_bytes)[0]
        fields = chunked_fields(struct.unpack(">"+"8sI"*fields_count_int, fields_bytes))
        source_xor = struct.unpack('>B', source_xor_bytes)[0]
    except ValueError:
        return InboxMessage(broken_message=True)
    except KeyError:
        return InboxMessage(broken_message=True)
    except struct.error:
        return InboxMessage(broken_message=True)

    return InboxMessage(header=header,
                        message_number=message_number,
                        source_name=source_name,
                        source_status= SOURCE_STATUSES.get(source_status, None),
                        fields_count=fields_count_int,
                        fields=fields,
                        source_xor=source_xor,
                        raw_payload = header_bytes
                                    + message_number_bytes
                                    + source_name_bytes
                                    + source_status_bytes
                                    + fields_count
                                    + fields_bytes
                        )


def unpack_inbox_sync(packet: bytes) -> InboxMessage:
    """
    >>> unpack_inbox_sync(bytes([0x01,  0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00,]))
    InboxMessage(header=1, message_number=1, source_name='', source_status='IDLE', fields_count=1, fields=[('', 0)], source_xor=0)
    """
    try:
        parsed = struct.unpack(_generate_sync_mask(packet[12]), packet)
    except ValueError:
        return InboxMessage(broken_message=True)
    except KeyError:
        return InboxMessage(broken_message=True)
    except struct.error:
        return InboxMessage(broken_message=True)

    header = parsed[0]
    mnum = parsed[1]
    source = btos(parsed[2])
    status = SOURCE_STATUSES.get(parsed[3], None)
    fields_count = parsed[4]
    fields =  chunked_fields(parsed[5:][:-1])
    checksum = parsed[-1]

    return InboxMessage(header=header,
                        message_number=mnum,
                        source_name=source,
                        source_status=status,
                        fields_count=fields_count,
                        fields=fields,
                        source_xor=checksum,
                        raw_payload=packet,
                        )


def pack_inbox(msg: InboxMessage) -> bytes:
    r"""
    >>> raw = bytes([0x01,  0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00,])
    >>> msg = InboxMessage(header=1, message_number=1, source_name='', source_status='IDLE', fields_count=1, fields=[('', 0)], source_xor=0, raw_payload=raw)
    >>> pack_inbox(msg)
    b'\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    """
    mask = _generate_sync_mask(msg.fields_count, with_checksum=False)
    body = struct.pack(mask,
                       msg.header,
                       msg.message_number,
                       stob(msg.source_name, 8),
                       REVERSE_SOURCE_STATUSES.get(msg.source_status),
                       msg.fields_count,
                       *flaten_fields(msg.fields),
                       )
    return body + xor(body)

def pack_inbox_fields(message: InboxMessage) -> Iterable[bytes]:
    for k, v in message.fields:
        yield encode_ascii(f"[{message.source_name}] {k} | {v}\r\n")


def pack_outbox(msg: OutboxMessage) -> bytes:
    r"""
    >>> pack_outbox(OutboxMessage(header=0x11, message_number=29))
    b'\x11\x00\x1d\x0c'
    """
    packed = struct.pack('>BH', msg.header, msg.message_number)
    return packed + xor(packed)


def pack_stats(stat: SourceStatistics) -> bytes:
    r"""
    >>> msg = pack_stats(SourceStatistics("test", "ACTIVE", 1, 1))
    >>> msg.startswith(b'[test] 1 | ACTIVE | ') and msg.endswith(b'\r\n')
    True
    """
    time_delta_in_ms = now() - stat.last_message_timestamp_in_ms
    return encode_ascii(
        f"[{stat.name}] "
        f"{stat.last_message_number} | "
        f"{stat.status} | "
        f"{time_delta_in_ms}"
        "\r\n"
    )
