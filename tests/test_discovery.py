from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtTest import QSignalSpy

from lenlab.controller import launchpad, linux
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


def test_no_rules(monkeypatch):
    monkeypatch.setattr(linux, "check_rules", lambda: False)
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoRules)

    monkeypatch.setattr(linux, "install_rules", lambda: None)
    error.callback()


def test_no_launchpad(monkeypatch):
    monkeypatch.setattr(linux, "check_rules", lambda: True)
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
    monkeypatch.setattr(linux, "check_rules", lambda: True)
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    monkeypatch.setattr(linux, "check_permission", lambda path: False)
    monkeypatch.setattr(linux, "check_group", lambda path: False)
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoGroup)

    monkeypatch.setattr(linux, "add_to_group", lambda path: None)
    error.callback()


def test_no_permission(monkeypatch):
    monkeypatch.setattr(linux, "check_rules", lambda: True)
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [MockSerialPortInfo()])
    monkeypatch.setattr(linux, "check_permission", lambda path: False)
    monkeypatch.setattr(linux, "check_group", lambda path: True)
    discovery = Discovery()

    spy = Spy(discovery.error)
    discovery.discover()
    error = spy.get_single_arg()
    assert isinstance(error, NoPermission)
