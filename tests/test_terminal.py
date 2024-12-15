import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSerialPort import QSerialPort

from lenlab.controller.terminal import PortError, Terminal
from lenlab.model.port_info import PortInfo
from lenlab.spy import Spy


def test_from_port_info():
    terminal = Terminal.from_port_info(PortInfo())
    assert isinstance(terminal, Terminal)
    assert hasattr(terminal, "port")
    assert isinstance(terminal.port, QSerialPort)


def test_open_fails():
    terminal = Terminal.from_port_info(PortInfo())
    spy = Spy(terminal.error)
    assert not terminal.open()
    assert spy.is_single_message(PortError)


class MockPort(QSerialPort):
    def open(self, mode):
        return True

    def close(self):
        pass

    def portName(self):
        return "ttySmock0"

    def setBaudRate(self, baudRate):
        assert isinstance(baudRate, int)

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


def test_port_interface(terminal):
    assert terminal.port_name == "ttySmock0"
    terminal.set_baud_rate(1_000_000)
    packet = terminal.peek(8)
    assert isinstance(packet, bytes)
    packet = terminal.read(8)
    assert isinstance(packet, bytes)
    terminal.write(b"command")
