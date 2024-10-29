from itertools import repeat

import numpy as np
import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad import KB, crc, knock_packet
from lenlab.lenlab import pack


@pytest.fixture(scope="module")
def memory(port: QSerialPort) -> np.ndarray:
    port.write(pack(b"mi28K"))  # init 28K
    reply = read(port, 8)
    assert reply == pack(b"mi28K")

    return np.fromiter(crc(repeat(0, (28 * KB - 8) // 4), n_bits=32), dtype=np.dtype("<u4"))


def read(port: QSerialPort, size: int, timeout: int = 300) -> bytes:
    while port.bytesAvailable() < size:
        if not port.waitForReadyRead(timeout):  # about 1 KB per event
            break

    return port.read(size).data()


def test_knock(firmware, port: QSerialPort):
    port.write(knock_packet)
    reply = read(port, 8)
    assert reply == knock_packet


@pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, cleanup, port: QSerialPort, memory: np.ndarray):
    # 4 MBaud: about 120 invalid packets per 100 MB
    #     round trip time: 120 ms, net transfer rate 230 KB/s
    # 1 MBaud: about 2 invalid packets per 100 MB
    #     round trip time: 320 ms, net transfer rate 90 KB/s
    port.write(pack(b"mg28K"))  # get 28K

    reply = read(port, 28 * KB)
    head = reply[:8]
    assert head == b"Lm\x00\x70g28K", "invalid reply"

    # there seem to be no corrupt but complete packets
    size = len(reply)
    assert size == 28 * KB, "incomplete packet"

    # little endian, unsigned int, 4 byte, offset 8 bytes
    payload = np.frombuffer(reply, np.dtype("<u4"), offset=8)
    if not np.all(payload == memory):
        raise AssertionError("complete packet, but corrupt data")
