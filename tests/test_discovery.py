from dataclasses import dataclass

from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtTest import QSignalSpy

from lenlab.controller import discovery as discovery_module
from lenlab.controller import launchpad
from lenlab.controller.discovery import (
    Discovery,
    NoGroup,
    NoLaunchpad,
    NoPermission,
    NoRules,
)


class Spy(QSignalSpy):
    def get_single_arg(self):
        if self.count() == 1:
            return self.at(0)[0]


@dataclass()
class MockLinux:
    _check_rules: bool = False
    _check_permission: bool = False
    _check_group: bool = False

    _install_rules_called: int = 0
    _add_to_group_called: int = 0

    @staticmethod
    def is_linux() -> bool:
        return True

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
    monkeypatch.setattr(discovery_module, "linux", MockLinux(True))
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
    monkeypatch.setattr(discovery_module, "linux", linux := MockLinux(True))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoGroup)

    error.callback()
    assert linux._add_to_group_called == 1


def test_no_permission(monkeypatch):
    monkeypatch.setattr(discovery_module, "linux", MockLinux(True, False, True))
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoPermission)
