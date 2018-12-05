
from core.types import InboxMessage
from core.types import SOURCE_STATUSES
from core.utils import xor


class UnmarshallingError(Exception):
    pass


class InboxError(Exception):
    pass

class WrongChecksum(InboxError):
    pass

class WrongStatus(InboxError):
    pass

class WrongHeader(InboxError):
    pass

class WrongFieldsAmount(InboxError):
    pass


def _validate_xor(body, xor_result) -> bool:
    """
    >>> _validate_xor(b'\x01\x01\x01', 1)
    True
    """
    return xor(body)[0] == xor_result

def validate_inbox(msg: InboxMessage):
    """
    >>> raw = bytes([0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  0x00,])
    >>> msg = InboxMessage(header=1, message_number=1, source_name='', source_status='IDLE', fields_count=1, fields=[('', 0)], source_xor=0, raw_payload=raw)
    >>> validate_inbox(msg)
    >>> msg = InboxMessage(header=2, message_number=1, source_name='', source_status='IDLE', fields_count=1, fields=[('', 0)], source_xor=0, raw_payload=raw)
    >>> validate_inbox(msg)
    Traceback (most recent call last):
     ...
    validators.WrongHeader
    >>> msg = InboxMessage(header=1, message_number=1, source_name='', source_status='WRONG', fields_count=1, fields=[('', 0)], source_xor=0, raw_payload=raw)
    >>> validate_inbox(msg)
    Traceback (most recent call last):
     ...
    validators.WrongStatus
    >>> msg = InboxMessage(header=1, message_number=1, source_name='', source_status='IDLE', fields_count=100, fields=[('', 0)], source_xor=0, raw_payload=raw)
    >>> validate_inbox(msg)
    Traceback (most recent call last):
     ...
    validators.WrongFieldsAmount
    >>> msg = InboxMessage(header=1, message_number=1, source_name='', source_status='IDLE', fields_count=1, fields=[('', 0)], source_xor=10, raw_payload=raw)
    >>> validate_inbox(msg)
    Traceback (most recent call last):
     ...
    validators.WrongChecksum
    """
    if msg.broken_message:
        raise UnmarshallingError
    if msg.header !=  0x01:
        raise WrongHeader
    if not _validate_xor(msg.raw_payload, msg.source_xor):
        raise WrongChecksum
    if msg.fields_count != len(msg.fields):
        raise WrongFieldsAmount
    if msg.source_status not in SOURCE_STATUSES.values():
        raise WrongStatus
