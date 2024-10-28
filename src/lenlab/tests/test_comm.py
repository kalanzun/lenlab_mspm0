from itertools import batched

import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab import launchpad
from lenlab.lenlab import pack

KB = 1024


# little endian, reversed polynom
crc_polynom = 0xEDB88320


def crc32(checksum: int = 0xFFFFFFFF):
    while True:
        # checksum = checksum ^ value
        for _ in range(32):
            mask = -(checksum & 1)
            checksum = (checksum >> 1) ^ (crc_polynom & mask)

        yield checksum


def read(port: QSerialPort, size: int, timeout: int = 100) -> bytes:
    while port.bytesAvailable() < size:
        if not port.waitForReadyRead(timeout):  # about 1 KB per event
            break

    return port.read(size).data()


def test_knock(firmware, port: QSerialPort):
    port.write(launchpad.knock_packet)
    reply = read(port, 8)
    assert reply == launchpad.knock_packet


def test_28kb_checksum(firmware, port: QSerialPort):
    port.write(pack(b"m28KB"))
    reply = read(port, 28 * KB)
    head = reply[:8]
    assert head == b"Lm\x00\x7028KB"

    size = len(reply)
    assert size == 28 * KB

    payload = reply[8:]
    for i, (word, checksum) in enumerate(zip(batched(payload, 4), crc32(), strict=False)):
        value = int.from_bytes(word, "little")
        assert value == checksum, f"false value at {i=}"


@pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28kb_error_rate(firmware, port: QSerialPort):
    # 4 MBaud: about 120 invalid packets per 100 MB
    #     round trip time: 120 ms, net transfer rate 230 KB/s
    # 1 MBaud: about 2 invalid packets per 100 MB
    #     round trip time: 320 ms, net transfer rate 90 KB/s
    port.write(pack(b"m28KB"))

    reply = read(port, 28 * KB)
    head = reply[:8]
    assert head == b"Lm\x00\x7028KB"

    # there seem to be no corrupt but complete packets
    size = len(reply)
    assert size == 28 * KB
