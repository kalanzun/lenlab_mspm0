import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSerialPort import QSerialPort
from PySide6.QtTest import QSignalSpy

from lenlab.launchpad import terminal as terminal_messages
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


class MockPort(QSerialPort):
    def __init__(self):
        super().__init__()

        self.open_result = True
        self.is_open = False

    def bytesAvailable(self):
        return 7

    def isOpen(self):
        return self.is_open

    def open(self, mode):
        self.is_open = self.open_result
        return self.open_result

    def close(self):
        self.is_open = False

    def clear(self):
        pass

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


@pytest.fixture
def error(terminal):
    error = Spy(terminal.error)
    return error


def test_open_fails(terminal, error):
    terminal.port.open_result = False

    terminal.open()  # connects the signals
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.NoError)
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.DeviceNotFoundError)

    assert not terminal.open()
    assert isinstance(error.get_single_arg(), terminal_messages.PortError)


def test_open_and_close(terminal, error):
    closed = QSignalSpy(terminal.closed)

    assert not terminal.is_open
    assert terminal.open()
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.NoError)

    assert terminal.is_open
    assert error.count() == 0

    assert terminal.open()
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.NoError)

    assert terminal.is_open
    assert error.count() == 0

    terminal.close()
    assert closed.count() == 1

    terminal.close()
    assert closed.count() == 1


def test_baud_rate(terminal):
    terminal.set_baud_rate(1_000_000)


def test_peek_and_read(terminal):
    n = terminal.bytes_available

    packet = terminal.peek(n)
    assert packet == b"example"

    packet = terminal.read(n)
    assert packet == b"example"


def test_write(terminal):
    terminal.write(b"command")


def test_permission_error(terminal, error):
    terminal.open()  # connects the signals
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.PermissionError)

    assert isinstance(error.get_single_arg(), terminal_messages.NoPermission)


def test_resource_error(terminal, error):
    terminal.open()  # connects the signals
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.ResourceError)

    assert isinstance(error.get_single_arg(), terminal_messages.ResourceError)

    assert not terminal.is_open


def test_terminal_error(terminal, error):
    terminal.open()  # connects the signals
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.UnknownError)

    assert isinstance(error.get_single_arg(), terminal_messages.PortError)

    assert not terminal.is_open


def test_from_port_info():
    terminal = Terminal.from_port_info(PortInfo())
    assert isinstance(terminal, Terminal)
