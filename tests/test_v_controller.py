import struct

import pytest
from PySide6.QtCore import QObject, Signal

from lenlab.launchpad.protocol import pack
from lenlab.launchpad.terminal import Terminal, TerminalResourceError
from lenlab.message import Message
from lenlab.model.lenlab import Lenlab
from lenlab.model.voltmeter import Voltmeter

struct_point = struct.Struct("<IHH")


def pack_point(i: int, t: int = 0, v1: int = 0, v2: int = 0):
    return b"Lv\x08\x00" + (b" red" if i % 2 == 0 else b" blu") + struct_point.pack(t, v1, v2)


class MockVoltmeterTerminal(Terminal):

    def __init__(self):
        super().__init__()
        self.index = 0
        self.interval = 0

    @property
    def is_open(self):
        return True

    def close(self) -> None:
        self.closed.emit()

    def write(self, packet: bytes):
        if packet == pack(b"vnext"):
            if self.index < 2:
                self.reply.emit(pack_point(self.index, self.index * self.interval))
                self.index += 1
            elif self.index == 2:
                self.reply.emit(pack(b"verr!"))
                self.index += 1
        elif packet == pack(b"vstop"):
            self.reply.emit(pack(b"vstop"))
        else:
            self.interval = int.from_bytes(packet[4:8], byteorder="little")
            self.reply.emit(pack(b"vstrt"))


@pytest.fixture()
def voltmeter():
    lenlab = Lenlab()
    voltmeter = Voltmeter(lenlab)
    return voltmeter


@pytest.fixture()
def opened(voltmeter):
    voltmeter.on_new_terminal(MockVoltmeterTerminal())


@pytest.fixture()
def started(voltmeter, opened):
    voltmeter.start(1000)


def test_start(voltmeter, started):
    assert voltmeter.active is True
    assert voltmeter.next_timer.isActive()


def test_start_no_terminal(voltmeter):
    with pytest.raises(RuntimeError):
        voltmeter.start(1000)


def test_start_already_started(voltmeter, started):
    with pytest.raises(RuntimeError):
        voltmeter.start(1000)


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


def test_stop_no_terminal(voltmeter):
    with pytest.raises(RuntimeError):
        voltmeter.stop()


def test_stop_already_stopped(voltmeter, stopped):
    with pytest.raises(RuntimeError):
        voltmeter.stop()


def test_close(voltmeter, started):
    voltmeter.terminal.close()

    assert voltmeter.active is False
    assert not voltmeter.next_timer.isActive()


def test_terminal_error(voltmeter, started):
    voltmeter.terminal.error.emit(TerminalResourceError)

    assert voltmeter.active is False
    assert not voltmeter.next_timer.isActive()


@pytest.fixture()
def error_reply(voltmeter, blu):
    voltmeter.next_timer.timeout.emit()  # trigger next timer


def test_error_reply(voltmeter, error_reply):
    assert voltmeter.active is True
    assert voltmeter.next_timer.isActive()

    assert len(voltmeter.points) == 2
