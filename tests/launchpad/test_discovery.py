import sys

import pytest

from lenlab.launchpad import discovery as discovery_messages
from lenlab.launchpad import rules
from lenlab.launchpad import terminal as terminal_messages
from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.launchpad import lp_pid, ti_vid, tiva_pid
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.protocol import get_example_version_reply
from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


@pytest.fixture(autouse=True)
def platform_any(monkeypatch):
    monkeypatch.setattr(sys, "platform", "any")


@pytest.fixture()
def platform_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(rules, "check_rules", lambda: True)


@pytest.fixture()
def no_rules(monkeypatch):
    monkeypatch.setattr(rules, "check_rules", lambda: False)


@pytest.fixture()
def platform_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")


@pytest.fixture()
def available_ports(monkeypatch):
    available_ports = []
    monkeypatch.setattr(PortInfo, "available_ports", lambda: available_ports)
    return available_ports


@pytest.fixture
def discovery(platform_any):
    return Discovery()


@pytest.fixture
def error(discovery):
    error = Spy(discovery.error)
    return error


def test_no_launchpad(available_ports, discovery, error):
    discovery.find()

    error.check_single_message(discovery_messages.NoLaunchpad)
    assert len(discovery.terminals) == 0


def test_retry_find(available_ports, discovery, error):
    discovery.retry()

    error.check_single_message(discovery_messages.NoLaunchpad)
    assert len(discovery.terminals) == 0


def test_port_argument(monkeypatch, available_ports, discovery, error):
    monkeypatch.setattr(PortInfo, "from_name", lambda name: PortInfo(name, is_available=True))

    discovery.port_name = "COM0"
    discovery.find()

    assert len(discovery.terminals) == 1


def test_not_found(available_ports, discovery, error):
    discovery.port_name = "COM0"
    discovery.find()

    error.check_single_message(discovery_messages.NotFound)
    assert len(discovery.terminals) == 0


def test_no_rules(platform_linux, no_rules, available_ports, discovery, error):
    discovery.find()

    error.check_single_message(discovery_messages.NoRules)
    assert len(discovery.terminals) == 0


def test_tiva_launchpad(available_ports, discovery, error):
    available_ports.append(PortInfo("COM0", ti_vid, tiva_pid))

    discovery.find()

    error.check_single_message(discovery_messages.TivaLaunchpad)
    assert len(discovery.terminals) == 0


def test_select_first(available_ports, discovery):
    available_ports.append(PortInfo("ttyS0", ti_vid, lp_pid))
    available_ports.append(PortInfo("ttyS1", ti_vid, lp_pid))

    discovery.find()

    assert len(discovery.terminals) == 1


def test_no_selection_on_windows(platform_win32, available_ports, discovery):
    available_ports.append(PortInfo("COM0", ti_vid, lp_pid))
    available_ports.append(PortInfo("COM1", ti_vid, lp_pid))

    discovery.find()

    assert len(discovery.terminals) == 2


class MockTerminal(Terminal):
    def open(self):
        return True

    def close(self):
        pass

    @property
    def is_open(self):
        return False

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


def test_retry_probe(discovery, terminal):
    spy = Spy(discovery.ready)

    discovery.retry()

    terminal.reply.emit(get_example_version_reply())

    assert spy.get_single_arg() is terminal


def test_probe_select(discovery, terminal):
    discovery.terminals.append(MockTerminal())

    spy = Spy(discovery.ready)

    discovery.probe()

    terminal.reply.emit(get_example_version_reply())

    assert spy.get_single_arg() is terminal
    assert len(discovery.terminals) == 1


def test_invalid_firmware_version(discovery, terminal, error):
    discovery.probe()

    reply = b"L8\x00\x00\x00\x00\x00\x00"
    terminal.reply.emit(reply)

    error.check_single_message(discovery_messages.InvalidVersion)


def test_invalid_reply(discovery, terminal, error):
    discovery.probe()

    reply = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    terminal.reply.emit(reply)

    error.check_single_message(discovery_messages.InvalidReply)


def test_terminal_error(discovery, terminal, error):
    discovery.open()
    discovery.probe()

    terminal.error.emit(terminal_messages.ResourceError())

    error.check_single_message(terminal_messages.ResourceError)


def test_no_firmware(discovery, terminal, error):
    discovery.probe()

    assert discovery.timer.isActive()
    discovery.timer.timeout.emit()

    error.check_single_message(discovery_messages.NoFirmware)


def test_open_fails(discovery, terminal, error):
    terminal.open = lambda: False

    discovery.open()

    terminal.error.emit(terminal_messages.NoPermission("COM0"))

    error.check_single_message(terminal_messages.NoPermission)
