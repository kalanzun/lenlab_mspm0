import pytest

from PySide6.QtSerialPort import QSerialPort


def packet(cmd: bytes):
    assert len(cmd) == 5
    return b"L\x01\x00" + cmd


class Terminal:
    def __init__(self, port: QSerialPort):
        self.port = port

    def wait_for_packet(self, length: int = 8, timeout: int = 200) -> bool:
        while self.port.bytesAvailable() < length:
            if not self.port.waitForReadyRead(timeout):
                self.port.readAll()  # clear out partial packet data
                return False  # timeout

        return True  # length bytes available

    def read(self) -> bytes:
        # do read extra data
        return self.port.readAll().data()

    def read_packet(self, length: int = 8, timeout: int = 200) -> bytes | None:
        if self.wait_for_packet(length, timeout):
            return self.read()

    def write(self, data: bytes):
        self.port.write(data)

    def wait_for_transmission(self, timeout: int = 200) -> bool:
        return self.port.waitForBytesWritten(timeout)


@pytest.fixture
def terminal(port) -> Terminal:
    return Terminal(port)


def test_knock(firmware, terminal: Terminal):
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_incomplete_packet(firmware, terminal: Terminal):
    terminal.write(b"L\x05\x00")
    assert not terminal.wait_for_packet()

    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_wrong_baudrate(firmware, terminal: Terminal):
    terminal.port.setBaudRate(4_000_000)
    terminal.write(packet(b"knock"))
    assert not terminal.wait_for_packet()

    terminal.port.setBaudRate(9_600)
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_hitchhiker(firmware, terminal: Terminal):
    terminal.write(packet(b"knock") + b"knock")
    assert terminal.read_packet() == packet(b"hello")

    assert not terminal.wait_for_packet()
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_reply_too_long(firmware, terminal: Terminal):
    terminal.write(packet(b"get10"))
    assert terminal.read_packet() == packet(b"get10")

    assert not terminal.wait_for_packet()
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_baudrate(firmware, terminal: Terminal):
    terminal.write(packet(b"b4MBd"))
    terminal.wait_for_transmission()

    terminal.port.setBaudRate(4_000_000)
    assert terminal.read_packet(timeout=300) == packet(b"b4MBd")
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")

    terminal.write(packet(b"b9600"))
    terminal.wait_for_transmission()

    terminal.port.setBaudRate(9_600)
    assert terminal.read_packet(timeout=300) == packet(b"b9600")


def test_probe(firmware, terminal: Terminal):
    terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert terminal.read_packet() == packet(b"hello")


def test_probe_bsl(bsl, terminal: Terminal):
    terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert terminal.read_packet(length=10) == bytes.fromhex("00 08 02 00 3B 06 0D A7 F7 6B")
