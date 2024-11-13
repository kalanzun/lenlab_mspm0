from itertools import repeat

import numpy as np

from .launchpad import KB, crc


def pack(argument: bytes, length: int = 0) -> bytes:
    assert len(argument) == 5
    return b"L" + argument[0:1] + length.to_bytes(2, byteorder="little") + argument[1:]


def make_memory_28k() -> np.ndarray:
    return np.fromiter(crc(repeat(0, (28 * KB - 8) // 4), n_bits=32), dtype=np.dtype("<u4"))


def check_memory_28k(reply: bytes, memory_28k: np.ndarray) -> None:
    head = reply[:8]
    expected = pack(b"mg28K", length=memory_28k.nbytes)
    assert head == expected, "invalid reply"

    # there seem to be no corrupt but complete packets
    payload_size = len(reply) - 8
    memory_size = memory_28k.nbytes
    assert payload_size == memory_size, "incomplete packet"

    # little endian, unsigned int, 4 byte, offset 8 bytes
    payload = np.frombuffer(reply, np.dtype("<u4"), offset=8)
    if not np.all(payload == memory_28k):
        raise AssertionError("corrupt data")
