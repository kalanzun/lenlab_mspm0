from itertools import repeat

import numpy as np

from lenlab.launchpad import crc
from lenlab.protocol import pack

KB = 1024


def memory_28k() -> np.ndarray:
    return np.fromiter(crc(repeat(0, (28 * KB - 8) // 4), n_bits=32), dtype=np.dtype("<u4"))


def check_memory(argument: bytes, memory: np.ndarray, reply: bytes):
    head = reply[:8]
    packet = pack(argument, length=memory.nbytes)
    assert head == packet, "invalid reply"

    # there seem to be no corrupt but complete packets
    payload_size = len(reply) - 8
    memory_size = memory.nbytes
    assert payload_size == memory_size, "incomplete packet"

    # little endian, unsigned int, 4 byte, offset 8 bytes
    payload = np.frombuffer(reply, np.dtype("<u4"), offset=8)
    if not np.all(payload == memory):
        raise AssertionError("complete packet, but corrupt data")
