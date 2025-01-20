import sys

import pytest

from lenlab.launchpad import discovery as discovery_module
from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.launchpad import lp_pid, ti_vid, tiva_pid
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.protocol import get_example_version_reply
from lenlab.launchpad.terminal import Terminal, TerminalPermissionError, TerminalResourceError
from lenlab.spy import Spy


@pytest.fixture(autouse=True)
def platform_any(monkeypatch):
    monkeypatch.setattr(sys, "platform", "any")


@pytest.fixture()
def platform_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")


@pytest.fixture()
def platform_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(discovery_module, "check_rules", lambda: True)


@pytest.fixture()
def no_rules(monkeypatch):
    monkeypatch.setattr(discovery_module, "check_rules", lambda: False)


@pytest.fixture()
def platform_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")


@pytest.fixture()
def available_ports(monkeypatch):
    available_ports = []
    monkeypatch.setattr(PortInfo, "available_ports", lambda: available_ports)
    return available_ports


@pytest.fixture
def discovery():
    return Discovery()


@pytest.fixture
def error(discovery):
    error = Spy(discovery.error)
    return error


def test_no_launchpad(available_ports, discovery, error):
    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_module.NoLaunchpad)
    assert discovery.terminals == []


def test_no_rules(platform_linux, no_rules, available_ports, discovery, error):
    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_module.NoRules)
    assert discovery.terminals == []


def test_tiva_launchpad(available_ports, discovery, error):
    available_ports.append(PortInfo("COM0", ti_vid, tiva_pid))

    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_module.TivaLaunchpad)
    assert discovery.terminals == []


def test_port_argument(available_ports):
    discovery = Discovery("COM0")

    discovery.find()

    assert len(discovery.terminals) == 1
    assert isinstance(discovery.terminals[0], Terminal)


def test_select_first(available_ports, discovery):
    available_ports.append(PortInfo("ttyS0", ti_vid, lp_pid))
    available_ports.append(PortInfo("ttyS1", ti_vid, lp_pid))

    discovery.find()

    assert len(discovery.terminals) == 1
    assert isinstance(discovery.terminals[0], Terminal)


def test_no_selection_on_windows(platform_win32, available_ports, discovery):
    available_ports.append(PortInfo("COM0", ti_vid, lp_pid))
    available_ports.append(PortInfo("COM1", ti_vid, lp_pid))

    discovery.find()

    assert len(discovery.terminals) == 2
    assert isinstance(discovery.terminals[0], Terminal)
    assert isinstance(discovery.terminals[1], Terminal)


class MockTerminal(Terminal):
    def open(self):
        return True

    def set_baud_rate(self, baud_rate: int) -> None:
        pass

    def write(self, packet: bytes) -> int:
        return len(packet)


@pytest.fixture()
def terminal(discovery):
    terminal = MockTerminal()
    discovery.terminals = [terminal]
    return terminal


def test_probe(discovery, terminal):
    spy = Spy(discovery.ready)

    discovery.probe()

    terminal.reply.emit(get_example_version_reply())

    assert spy.get_single_arg() is terminal


def test_invalid_firmware_version(discovery, terminal, error):
    discovery.probe()

    reply = b"L8\x00\x00\x00\x00\x00\x00"
    terminal.reply.emit(reply)

    assert isinstance(error.get_single_arg(), discovery_module.InvalidFirmwareVersion)


def test_invalid_reply(discovery, terminal, error):
    discovery.probe()

    reply = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    terminal.reply.emit(reply)

    assert isinstance(error.get_single_arg(), discovery_module.InvalidReply)


def test_terminal_error(discovery, terminal, error):
    discovery.probe()

    terminal.error.emit(TerminalResourceError())

    assert isinstance(error.get_single_arg(), TerminalResourceError)


def test_no_firmware(discovery, terminal, error):
    discovery.probe()

    assert discovery.timer.isActive()
    discovery.timer.timeout.emit()

    assert isinstance(error.get_single_arg(), discovery_module.NoFirmware)


def test_open_fails(discovery, terminal, error):
    terminal.open = lambda: False

    discovery.probe()

    terminal.error.emit(TerminalPermissionError())

    assert isinstance(error.get_single_arg(), TerminalPermissionError)


def test_ignore_replies_when_inactive(discovery):
    spy = Spy(discovery.ready)

    discovery.on_reply(get_example_version_reply())

    assert spy.count() == 0


def test_ignore_errors_when_inactive(discovery, error):
    discovery.on_error(TerminalResourceError())

    assert error.count() == 0
