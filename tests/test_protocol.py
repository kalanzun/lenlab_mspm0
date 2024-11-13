from itertools import repeat

import numpy as np
import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad import KB, crc
from lenlab.protocol import pack

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
knock_packet = b"Lk\x00\x00nock"


def test_bsl_resilience_to_false_baud_rate(bsl, port: QSerialPort):
    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert not port.waitForReadyRead(100), "BSL should not reply"

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert port.waitForReadyRead(100), "BSL should reply"

    # assume cold BSL
    # warm BSL for further tests
    reply = port.readAll().data()
    assert reply == b"\x00"


def test_firmware_resilience_to_false_baud_rate(firmware, port: QSerialPort):
    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert not port.waitForReadyRead(100), "Firmware should not reply"

    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert port.waitForReadyRead(100), "Firmware should reply"

    reply = port.readAll().data()
    assert reply == knock_packet


def test_knock(firmware, send, receive):
    send(knock_packet)
    reply = receive(len(knock_packet))
    assert reply == knock_packet


@pytest.fixture(scope="session")
def memory_28k(firmware, send, receive):
    send(packet := pack(b"mi28K"))  # init 28K
    reply = receive(8)
    assert reply == packet

    return np.fromiter(crc(repeat(0, (28 * KB - 8) // 4), n_bits=32), dtype=np.dtype("<u4"))


# @pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, send, receive, memory_28k):
    # 4 MBaud: about 120 invalid packets per 100 MB
    #     round trip time: 120 ms, net transfer rate 230 KB/s
    # 1 MBaud: about 2 invalid packets per 100 MB
    #     round trip time: 320 ms, net transfer rate 90 KB/s
    send(pack(b"mg28K"))  # get 28K
    reply = receive(28 * KB, timeout=300)

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
