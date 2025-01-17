import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSerialPort import QSerialPort

from lenlab.controller.terminal import PortError, Terminal
from lenlab.model.port_info import PortInfo
from lenlab.spy import Spy


def test_open_fails():
    terminal = Terminal().init_port_info(PortInfo())
    spy = Spy(terminal.error)
    assert not terminal.open()
    assert spy.is_single_message(PortError)


class MockPort(QSerialPort):
    def open(self, mode):
        return True

    def close(self):
        pass

    def portName(self):
        return "COM0"

    def setBaudRate(self, baudRate):
        assert isinstance(baudRate, int)

    def bytesAvailable(self):
        return 7

    def peek(self, maxlen):
        return QByteArray(b"example")

    def read(self, maxlen):
        return QByteArray(b"example")

    def write(self, data):
        assert isinstance(data, bytes)


@pytest.fixture
def terminal():
    terminal = Terminal()
    terminal.port = MockPort()
    return terminal


def test_open(terminal):
    assert terminal.open()


def test_close(terminal):
    terminal.close()


def test_port_name(terminal):
    assert terminal.port_name == "COM0"


def test_baud_rate(terminal):
    terminal.set_baud_rate(1_000_000)


def test_peek_and_read(terminal):
    n = terminal.bytes_available()

    packet = terminal.peek(n)
    assert packet == b"example"

    packet = terminal.read(n)
    assert packet == b"example"


def test_write(terminal):
    terminal.write(b"command")
