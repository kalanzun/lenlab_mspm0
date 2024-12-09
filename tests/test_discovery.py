from dataclasses import dataclass

from PySide6.QtCore import QEventLoop
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtTest import QSignalSpy

from lenlab.controller import discovery as discovery_module
from lenlab.controller import launchpad
from lenlab.controller.discovery import (
    Discovery,
    InvalidFirmwareVersion,
    NoFirmware,
    NoGroup,
    NoLaunchpad,
    NoPermission,
    NoRules,
)
from lenlab.controller.protocol import get_app_version
from lenlab.controller.terminal import Terminal, TerminalPermissionError


class Spy(QSignalSpy):
    def get_single_arg(self):
        if self.count() == 1:
            return self.at(0)[0]


@dataclass()
class MockLinux:
    _is_linux: bool = True
    _check_rules: bool = False
    _check_permission: bool = False
    _check_group: bool = False

    _install_rules_called: int = 0
    _add_to_group_called: int = 0

    def is_linux(self) -> bool:
        return self._is_linux

    def check_rules(self) -> bool:
        return self._check_rules

    def install_rules(self) -> None:
        self._install_rules_called += 1

    def check_permission(self, path) -> bool:
        return self._check_permission

    def check_group(self, path) -> bool:
        return self._check_group

    @staticmethod
    def get_group(path) -> str:
        return "dialout"

    @staticmethod
    def get_user_name() -> str:
        return "name"

    def add_to_group(self, path) -> None:
        self._add_to_group_called += 1


def test_no_rules(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", linux := MockLinux())
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoRules)

    error.callback()
    assert linux._install_rules_called == 1


def test_no_launchpad(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(True, True))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [])
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoLaunchpad)


class MockSerialPortInfo(QSerialPortInfo):
    def vendorIdentifier(self):
        return launchpad.ti_vid

    def productIdentifier(self):
        return launchpad.ti_pid

    def portName(self):
        return "ttyS0"

    def systemLocation(self):
        return "/dev/ttyS0"


def test_no_group(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", linux := MockLinux(True, True))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoGroup)

    error.callback()
    assert linux._add_to_group_called == 1


def test_no_permission(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(True, True, False, True))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoPermission)


class MockTerminalPermissionError(Terminal):
    def open(self) -> bool:
        self.error.emit(TerminalPermissionError())
        return False

    def close(self) -> None:
        pass


def test_open_error(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(False))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    monkeypatch.setattr(discovery_module, "QSerialPort", lambda port_info: port_info)
    monkeypatch.setattr(discovery_module, "Terminal", MockTerminalPermissionError)
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, TerminalPermissionError)


class MockTerminalNoReply(Terminal):
    def open(self) -> bool:
        return True

    def close(self) -> None:
        pass

    def set_baud_rate(self, baud_rate: int) -> None:
        pass

    def write(self, packet: bytes) -> None:
        pass


def test_no_reply(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(False))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    monkeypatch.setattr(discovery_module, "QSerialPort", lambda port_info: port_info)
    monkeypatch.setattr(discovery_module, "Terminal", MockTerminalNoReply)
    discovery = Discovery()
    discovery.discover()

    loop = QEventLoop()
    discovery.error.connect(lambda error: loop.quit())

    spy = Spy(discovery.error)
    loop.exec()
    error = spy.get_single_arg()
    assert isinstance(error, NoFirmware)


class MockTerminalInvalidVersion(Terminal):
    def open(self) -> bool:
        return True

    def close(self) -> None:
        pass

    def set_baud_rate(self, baud_rate: int) -> None:
        pass

    def write(self, packet: bytes) -> None:
        self.packet = packet
        self.on_ready_read()

    @property
    def bytes_available(self) -> int:
        return len(self.packet)

    def peek(self, n: int) -> bytes:
        return self.packet[:n]

    def read(self, n: int) -> bytes:
        chunk, self.packet = self.packet[:n], self.packet[n:]
        return chunk


def test_invalid_version(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(False))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    monkeypatch.setattr(discovery_module, "QSerialPort", lambda port_info: port_info)
    monkeypatch.setattr(discovery_module, "Terminal", MockTerminalInvalidVersion)
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, InvalidFirmwareVersion)


class MockTerminal(MockTerminalInvalidVersion):
    def write(self, packet: bytes) -> None:
        version = get_app_version().encode("ascii")[2:].ljust(4, b"\x00")
        self.packet = packet[0:4] + version
        self.on_ready_read()


def test_discovery(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(False))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    monkeypatch.setattr(discovery_module, "QSerialPort", lambda port_info: port_info)
    monkeypatch.setattr(discovery_module, "Terminal", MockTerminal)
    discovery = Discovery()

    spy = Spy(discovery.ready)
    discovery.discover()
    terminal = spy.get_single_arg()
    assert terminal
