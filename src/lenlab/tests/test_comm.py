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


def test_knock(firmware, port: QSerialPort):
    port.write(launchpad.knock_packet)
    while port.bytesAvailable() < 8:
        assert port.waitForReadyRead(100), "no reply received"
    reply = port.readAll().data()
    assert reply == launchpad.knock_packet


# @pytest.mark.repeat(4096)
def test_28kb(firmware, port: QSerialPort):
    port.write(pack(b"m28KB"))
    while port.bytesAvailable() < 28 * KB:
        if not port.waitForReadyRead(100):
            break
    reply = port.readAll().data()
    assert len(reply) == 28 * KB

    for i, (word, checksum) in enumerate(zip(batched(reply[8:], 4), crc32(), strict=False)):
        value = int.from_bytes(word, "little")
        assert value == checksum, f"{i=}"
