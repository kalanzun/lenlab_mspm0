import sys

import pytest

from lenlab.launchpad.discovery import (
    Discovery,
    InvalidFirmwareVersion,
    InvalidReply,
    NoFirmware,
    NoLaunchpad,
    TivaLaunchpad,
)
from lenlab.launchpad.launchpad import lp_pid, ti_vid, tiva_pid
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.protocol import get_app_version
from lenlab.launchpad.terminal import Terminal, TerminalPermissionError, TerminalResourceError
from lenlab.spy import Spy


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

    assert error.is_single_message(NoLaunchpad)
    assert discovery.available_terminals == []


def test_tiva_launchpad(available_ports, discovery, error):
    available_ports.append(PortInfo("COM0", ti_vid, tiva_pid))

    discovery.find()

    assert error.is_single_message(TivaLaunchpad)
    assert discovery.available_terminals == []


def test_port_argument(available_ports):
    discovery = Discovery("COM0")

    discovery.find()

    assert len(discovery.available_terminals) == 1
    assert isinstance(discovery.available_terminals[0], Terminal)


@pytest.fixture()
def win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")


@pytest.fixture()
def linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")


def test_select_first(available_ports, discovery, linux):
    available_ports.append(PortInfo("ttyS0", ti_vid, lp_pid))
    available_ports.append(PortInfo("ttyS1", ti_vid, lp_pid))

    discovery.find()

    assert len(discovery.available_terminals) == 1
    assert isinstance(discovery.available_terminals[0], Terminal)


def test_no_selection_on_windows(available_ports, discovery, win32):
    available_ports.append(PortInfo("COM0", ti_vid, lp_pid))
    available_ports.append(PortInfo("COM1", ti_vid, lp_pid))

    discovery.find()

    assert len(discovery.available_terminals) == 2
    assert isinstance(discovery.available_terminals[0], Terminal)
    assert isinstance(discovery.available_terminals[1], Terminal)


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
    discovery.available_terminals = [terminal]
    return terminal


def test_probe(discovery, terminal):
    spy = Spy(discovery.result)

    discovery.probe()

    version = get_app_version()
    reply = b"L8\x00\x00" + version[2:].encode("ascii").ljust(4, b"\x00")
    terminal.reply.emit(reply)

    assert spy.get_single_arg() is terminal


def test_invalid_firmware_version(discovery, terminal, error):
    discovery.probe()

    reply = b"L8\x00\x00\x00\x00\x00\x00"
    terminal.reply.emit(reply)

    assert error.is_single_message(InvalidFirmwareVersion)


def test_invalid_reply(discovery, terminal, error):
    discovery.probe()

    reply = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    terminal.reply.emit(reply)

    assert error.is_single_message(InvalidReply)


def test_terminal_error(discovery, terminal, error):
    discovery.probe()

    terminal.error.emit(TerminalResourceError())

    assert error.is_single_message(TerminalResourceError)


def test_no_firmware(discovery, terminal, error):
    discovery.probe()

    assert discovery.timer.isActive()
    discovery.timer.timeout.emit()

    assert error.is_single_message(NoFirmware)


def test_open_fails(discovery, terminal, error):
    terminal.open = lambda: False

    discovery.probe()

    terminal.error.emit(TerminalPermissionError())

    assert error.is_single_message(TerminalPermissionError)


def test_ignore_replies_when_inactive(discovery):
    spy = Spy(discovery.result)

    version = get_app_version()
    reply = b"L8\x00\x00" + version[2:].encode("ascii").ljust(4, b"\x00")
    discovery.on_reply(reply)

    assert spy.count() == 0


def test_ignore_errors_when_inactive(discovery, error):
    discovery.on_error(TerminalResourceError())

    assert error.count() == 0
