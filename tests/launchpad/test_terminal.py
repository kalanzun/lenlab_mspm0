import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad import terminal as terminal_messages
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


@pytest.fixture
def terminal():
    return Terminal.from_port_info(PortInfo.from_name("COM0"))


@pytest.fixture
def error(terminal):
    error = Spy(terminal.error)
    return error


def test_bytes_available(terminal):
    assert terminal.bytes_available == 0


def test_is_open(terminal):
    assert not terminal.is_open


def test_port_name(terminal):
    assert terminal.port_name == "COM0"


def test_open_fails(terminal, error):
    terminal.open()
    error.check_single_message(terminal_messages.PortError)


def test_open(monkeypatch, terminal, error):
    monkeypatch.setattr(QSerialPort, "open", lambda self, mode: True)
    monkeypatch.setattr(QSerialPort, "clear", lambda self: None)

    terminal.open()
    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.NoError)

    assert error.count() == 0


def test_close(monkeypatch, terminal, error):
    monkeypatch.setattr(QSerialPort, "isOpen", lambda self: True)
    monkeypatch.setattr(QSerialPort, "close", lambda self: None)

    terminal.close()

    assert error.count() == 0


def test_set_baud_rate(terminal):
    terminal.set_baud_rate(1_000_000)


def test_peek(monkeypatch, terminal):
    monkeypatch.setattr(QSerialPort, "peek", lambda self, n: QByteArray(b"example"))
    packet = terminal.peek(7)
    assert packet == b"example"


def test_read(monkeypatch, terminal):
    monkeypatch.setattr(QSerialPort, "read", lambda self, n: QByteArray(b"example"))
    packet = terminal.read(7)
    assert packet == b"example"


def test_write(monkeypatch, terminal):
    monkeypatch.setattr(QSerialPort, "write", lambda self, data: None)
    terminal.write(b"command")


def test_no_permission(monkeypatch, terminal, error):
    monkeypatch.setattr(QSerialPort, "isOpen", lambda self: True)
    terminal.open()  # connects the signals

    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.PermissionError)

    error.check_single_message(terminal_messages.NoPermission)


def test_resource_error(monkeypatch, terminal, error):
    monkeypatch.setattr(QSerialPort, "isOpen", lambda self: True)
    monkeypatch.setattr(QSerialPort, "close", lambda self: None)
    terminal.open()  # connects the signals

    terminal.port.errorOccurred.emit(QSerialPort.SerialPortError.ResourceError)

    error.check_single_message(terminal_messages.ResourceError)
