import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad import KB
from lenlab.protocol import check_memory_28k, make_memory_28k, pack

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
knock_packet = b"Lk\x00\x00nock"


@pytest.fixture(scope="module")
def send(port):
    def send(command: bytes):
        port.write(command)

    return send


@pytest.fixture(scope="module")
def receive(port):
    def receive(n: int, timeout: int = 100) -> bytes:
        while port.bytesAvailable() < n:
            if not port.waitForReadyRead(timeout):
                raise TimeoutError(f"{port.bytesAvailable()} bytes of {n} bytes received")
        return port.read(n).data()

    return receive


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


@pytest.fixture(scope="module")
def memory_28k(firmware, send, receive):
    send(packet := pack(b"mi28K"))  # init 28K
    reply = receive(8)
    assert reply == packet

    return make_memory_28k()


# @pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, send, receive, memory_28k):
    # 4 MBaud: about 120 invalid packets per 100 MB
    #     round trip time: 120 ms, net transfer rate 230 KB/s
    # 1 MBaud: about 2 invalid packets per 100 MB
    #     round trip time: 320 ms, net transfer rate 90 KB/s
    send(pack(b"mg28K"))  # get 28K
    reply = receive(28 * KB, timeout=400)
    check_memory_28k(reply, memory_28k)
