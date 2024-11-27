import struct

import pytest
from PySide6.QtCore import QObject, Signal

from lenlab.launchpad.protocol import pack
from lenlab.message import Message
from lenlab.model.lenlab import Lenlab
from lenlab.model.voltmeter import Voltmeter

struct_point = struct.Struct("<IHH")


def pack_point(i: int, t: int = 0, v1: int = 0, v2: int = 0):
    return b"Lv\x08\x00" + (b" red" if i % 2 == 0 else b" blu") + struct_point.pack(t, v1, v2)


class MockVoltmeterTerminal(QObject):
    error = Signal(Message)
    reply = Signal(bytes)
    closed = Signal()

    def __init__(self):
        super().__init__()
        self.port_is_open = True
        self.interval = 0
        self.i = 0

    @property
    def is_open(self):
        return self.port_is_open

    def close(self):
        if self.port_is_open:
            self.port_is_open = False
            self.closed.emit()

    def write(self, packet: bytes):
        if packet == pack(b"vnext"):
            self.reply.emit(pack_point(self.i, self.i * self.interval))
            self.i += 1
        elif packet == pack(b"vstop"):
            self.reply.emit(pack(b"vstop"))
        else:
            self.interval = int.from_bytes(packet[4:8], byteorder="little")
            self.reply.emit(pack(b"vstrt"))


@pytest.fixture()
def mock_terminal():
    return MockVoltmeterTerminal()


@pytest.fixture()
def voltmeter(mock_terminal):
    lenlab = Lenlab()
    voltmeter = Voltmeter(lenlab)
    voltmeter.error.connect(print)
    voltmeter.on_new_terminal(mock_terminal)
    return voltmeter


@pytest.fixture()
def started(voltmeter, mock_terminal):
    voltmeter.start(1000)


def test_start(voltmeter, started):
    assert voltmeter.active is True
    assert voltmeter.next_timer.isActive()


@pytest.fixture()
def red(voltmeter, started):
    voltmeter.next_timer.timeout.emit()  # trigger next timer


def test_red(voltmeter, red):
    assert voltmeter.active is True
    assert voltmeter.next_timer.isActive()

    assert len(voltmeter.points) == 1
    point = voltmeter.points[0]
    assert point.time == 0.0
    assert point[0] == 0.0
    assert point[1] == 0.0


@pytest.fixture()
def blu(voltmeter, red):
    voltmeter.next_timer.timeout.emit()  # trigger next timer


def test_blu(voltmeter, blu):
    assert voltmeter.active is True
    assert voltmeter.next_timer.isActive()

    assert len(voltmeter.points) == 2
    point = voltmeter.points[1]
    assert point.time == 1.0
    assert point[0] == 0.0
    assert point[1] == 0.0


@pytest.fixture()
def stopped(voltmeter, started):
    voltmeter.stop()


def test_stop(voltmeter, stopped):
    assert voltmeter.active is False
    assert not voltmeter.next_timer.isActive()


def test_close(voltmeter, started):
    voltmeter.terminal.close()

    assert voltmeter.active is False
    assert not voltmeter.next_timer.isActive()
