from itertools import repeat
from logging import getLogger

import numpy as np
import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab import launchpad
from lenlab.lenlab import pack

KB = 1024

logger = getLogger(__name__)


@pytest.fixture(scope="module")
def memory(port: QSerialPort):
    port.write(pack(b"mi28K"))  # init 28K
    reply = read(port, 8)
    assert reply == pack(b"mi28K")

    return np.fromiter(launchpad.crc(repeat(0, (28 * KB - 8) // 4), n_bits=32), dtype=np.dtype("<u4"))


def read(port: QSerialPort, size: int, timeout: int = 300) -> bytes:
    while port.bytesAvailable() < size:
        if not port.waitForReadyRead(timeout):  # about 1 KB per event
            break

    return port.read(size).data()


def test_knock(firmware, port: QSerialPort):
    port.write(launchpad.knock_packet)
    reply = read(port, 8)
    assert reply == launchpad.knock_packet


@pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28kb(firmware, port: QSerialPort, memory):
    # 4 MBaud: about 120 invalid packets per 100 MB
    #     round trip time: 120 ms, net transfer rate 230 KB/s
    # 1 MBaud: about 2 invalid packets per 100 MB
    #     round trip time: 320 ms, net transfer rate 90 KB/s
    try:
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
            logger.warning("complete packet and corrupt data")
            raise AssertionError("complete packet and corrupt data")

    except Exception:
        spurious = read(port, 28 * KB)
        if spurious:
            logger.warning("spurious bytes after timeout")

        raise
