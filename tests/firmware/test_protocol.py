import pytest
from PySide6.QtSerialPort import QSerialPort

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
knock_packet = b"Lk\x08\x00nock, knock!"
knock_reply = b"Lk\x00\x00nock"


@pytest.fixture(scope="module")
def send(port):
    def send(command: bytes):
        port.write(command)

    return send


@pytest.fixture(scope="module")
def receive(port):
    def receive(n: int, timeout: int = 400) -> bytes:
        while port.bytesAvailable() < n:
            if not port.waitForReadyRead(timeout):
                raise TimeoutError(f"{port.bytesAvailable()} bytes of {n} bytes received")
        return port.read(n).data()

    return receive


def test_bsl_resilience_to_false_baud_rate(bsl, port: QSerialPort):
    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert not port.waitForReadyRead(400), "BSL should not reply"

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert port.waitForReadyRead(400), "BSL should reply"

    # assume cold BSL
    # warm BSL for further tests
    reply = port.readAll().data()
    assert reply == b"\x00"


def test_firmware_resilience_to_false_baud_rate(firmware, port: QSerialPort):
    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert not port.waitForReadyRead(400), "Firmware should not reply"

    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert port.waitForReadyRead(400), "Firmware should reply"

    reply = port.readAll().data()
    assert reply == knock_reply


def test_knock(firmware, send, receive):
    send(knock_packet)
    reply = receive(len(knock_reply))
    assert reply == knock_reply
