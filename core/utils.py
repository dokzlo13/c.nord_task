
import time
from functools import reduce


def now() -> int:
    return round(time.time() * 1000)

def encode_ascii(str_obj: str) -> bytes:
    """
    >>> encode_ascii('hello!')
    b'hello!'
    """
    return str_obj.encode("ascii", "ignore")

def decode_ascii(bytes_obj: bytes) -> str:
    """
    >>> decode_ascii(b'hello!')
    'hello!'
    """
    return bytes_obj.decode("ascii", "ignore")


def btos(bytes: bytes) -> str:
    r"""
    >>> btos(b'\x00\x00\x00hello')
    'hello'
    """
    return bytes.lstrip(b"\x00").decode("ascii", "ignore")

def stob(string: str, length: int) -> bytes:
    r"""
    >>> stob('hello', 8)
    b'\x00\x00\x00hello'
    """
    if len(string) > length:
        raise ValueError(f"ascii string {string} greater then length limit {length}")
    return string.encode("ascii", "ignore").rjust(length, b"\x00")

def xor(bytes_obj: bytes) -> bytes:
    """
    >>> xor(bytes([0x01, 0x04, 0x03]))
    b'\\x06'
    """
    if len(bytes_obj) < 2:
        raise ValueError
    head, *tail = bytes_obj
    return bytes([reduce(lambda x, y: x ^ y, tail, head)])

