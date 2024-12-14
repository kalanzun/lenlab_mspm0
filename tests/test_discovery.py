import pytest
from PySide6.QtTest import QSignalSpy

from lenlab.controller.lenlab import InvalidFirmwareVersion, NoLaunchpad, NoReply
from lenlab.controller.terminal import PortError, Terminal
from lenlab.model.launchpad import ti_pid, ti_vid
from lenlab.model.port_info import PortInfo
from lenlab.model.protocol import get_app_version


class Spy(QSignalSpy):
    def get_single_arg(self):
        if self.count() == 1:
            return self.at(0)[0]

    def is_single_message(self, __class) -> bool:
        return isinstance(self.get_single_arg(), __class)


@pytest.fixture()
def available_ports(monkeypatch):
    ap = list()
    monkeypatch.setattr(PortInfo, "available_ports", lambda: ap)
    return ap


@pytest.fixture()
def mock_port_info(available_ports):
    available_ports.append(PortInfo("ttySmock0", ti_vid, ti_pid))


class MockTerminal(Terminal):
    open_result = False

    def open(self) -> bool:
        return self.open_result

    def set_baud_rate(self, baud_rate: int) -> None:
        pass

    def write(self, packet: bytes) -> None:
        pass


@pytest.fixture()
def mock_terminal(monkeypatch):
    terminal = MockTerminal()
    monkeypatch.setattr(Terminal, "from_port_info", lambda port_info: terminal)
    return terminal


def test_discover(lenlab, mock_port_info, mock_terminal):
    mock_terminal.open_result = True
    lenlab.discover()
    assert hasattr(lenlab, "terminal")
    assert isinstance(lenlab.terminal, MockTerminal)


def test_open_error(lenlab, mock_port_info, mock_terminal):
    lenlab.discover()
    assert not hasattr(lenlab, "terminal")


def test_no_launchpad(lenlab, available_ports):
    spy = Spy(lenlab.error)
    lenlab.discover()
    assert spy.is_single_message(NoLaunchpad)


def test_version_reply(lenlab):
    version = get_app_version()
    reply = b"L8\x00\x00" + version[2:].encode("ascii").ljust(4, b"\x00")

    spy = Spy(lenlab.ready)
    lenlab.on_reply(reply)
    assert spy.count() == 1


def test_invalid_version(lenlab):
    reply = b"L8\x00\x00\x00\x00\x00\x00"

    spy = Spy(lenlab.error)
    lenlab.on_reply(reply)
    assert spy.is_single_message(InvalidFirmwareVersion)


def test_port_error(lenlab):
    spy = Spy(lenlab.error)
    lenlab.on_error(PortError())
    assert spy.is_single_message(PortError)


def test_timeout(lenlab):
    spy = Spy(lenlab.error)
    lenlab.timer.timeout.emit()
    assert spy.is_single_message(NoReply)
