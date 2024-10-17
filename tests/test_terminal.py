from typing import Iterable

from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from pytest import fixture, mark


def find_vid_pid(vid: int, pid: int) -> Iterable[QSerialPortInfo]:
    for port_info in QSerialPortInfo.availablePorts():
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid:
            yield port_info


def connect() -> QSerialPort:
    port_infos = list(find_vid_pid(0x0451, 0xBEF3))
    assert len(port_infos) == 2

    aux_port_info, port_info = port_infos
    port = QSerialPort(port_info)
    port.setBaudRate(9600)

    assert port.open(QIODeviceBase.OpenModeFlag.ReadWrite)
    return port


@fixture()
def port() -> QSerialPort:
    return connect()


class Terminal:
    def __init__(self, port: QSerialPort):
        self.port = port

    def read(self) -> bytes:
        return self.port.readAll().data()

    def write(self, data: bytes):
        self.port.write(data)

    def wait_for_packet(self, timeout=200):
        while self.port.bytesAvailable() < 8:
            if not self.port.waitForReadyRead(timeout):
                self.port.readAll()  # clear out partial packet data
                return False  # timeout

        return True  # 8 bytes available

    def wait_for_transmission(self, timeout=200):
        return self.port.waitForBytesWritten(timeout)

    def knock(self):
        self.port.write(packet(b"knock"))
        assert self.wait_for_packet()
        reply = self.read()
        assert reply == packet(b"hello")


@fixture()
def terminal(port) -> Terminal:
    return Terminal(port)


def packet(cmd: bytes):
    assert len(cmd) == 5
    return b"L\x01\x00" + cmd


@mark.fw
def test_knock(terminal: Terminal):
    terminal.knock()


@mark.fw
def test_incomplete_packet(terminal: Terminal):
    terminal.write(b"L\x05\x00")
    assert not terminal.wait_for_packet()

    terminal.knock()


@mark.fw
def test_wrong_baudrate(terminal: Terminal):
    terminal.port.setBaudRate(4_000_000)
    terminal.write(packet(b"knock"))
    assert not terminal.wait_for_packet()

    terminal.port.setBaudRate(9_600)
    terminal.knock()


@mark.fw
def test_hitchhiker(terminal: Terminal):
    terminal.write(packet(b"knock") + b"knock")
    assert terminal.wait_for_packet()
    reply = terminal.read()
    assert reply == packet(b"hello")

    assert not terminal.wait_for_packet()

    terminal.knock()


@mark.fw
def test_reply_too_long(terminal: Terminal):
    terminal.write(packet(b"get10"))
    assert terminal.wait_for_packet()
    reply = terminal.read()
    assert reply == packet(b"get10")

    assert not terminal.wait_for_packet()

    terminal.knock()


@mark.fw
def test_baudrate(terminal: Terminal):
    terminal.write(packet(b"b4MBd"))
    terminal.wait_for_transmission()

    terminal.port.setBaudRate(4_000_000)
    terminal.wait_for_packet(300)
    reply = terminal.read()
    assert reply == packet(b"b4MBd")

    terminal.knock()

    terminal.write(packet(b"b9600"))
    terminal.wait_for_transmission()

    terminal.port.setBaudRate(9_600)
    terminal.wait_for_packet(300)
    reply = terminal.read()
    assert reply == packet(b"b9600")


@mark.fw
def test_probe(terminal: Terminal):
    terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert terminal.wait_for_packet()
    reply = terminal.read()
    assert reply == packet(b"hello")


@mark.bsl
def test_probe_bsl(terminal: Terminal):
    terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert terminal.port.waitForReadyRead(200)
    reply = terminal.read()
    assert reply == b"\x00" or reply == b"\x00\x08\x02\x00;\x06\r\xa7"
