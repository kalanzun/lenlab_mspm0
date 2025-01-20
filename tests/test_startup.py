import sys

import pytest
from attrs import frozen
from PySide6.QtCore import QByteArray
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.launchpad import lp_pid, ti_vid
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.protocol import get_example_version_reply
from lenlab.spy import Spy


@pytest.fixture()
def available_ports(monkeypatch):
    available_ports = []
    monkeypatch.setattr(PortInfo, "available_ports", lambda: available_ports)
    return available_ports


@pytest.fixture()
def darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")


@pytest.fixture()
def linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")


@pytest.fixture()
def win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")


class MockPort(QSerialPort):
    def __init__(self, reply: bytes | None = None):
        super().__init__()

        self.reply = reply

    def open(self, mode):
        return True

    def clear(self) -> None:
        pass

    def setBaudRate(self, baudRate: int) -> None:
        pass

    def write(self, packet: bytes) -> int:
        if self.reply is not None:
            self.readyRead.emit()

        return len(packet)

    def bytesAvailable(self) -> int:
        return len(self.reply)

    def peek(self, maxlen: int) -> QByteArray:
        return QByteArray(self.reply[:maxlen])

    def read(self, maxlen: int) -> QByteArray:
        reply, self.reply = self.reply[:maxlen], self.reply[maxlen:]
        return QByteArray(reply)


@frozen
class MockPortInfo(PortInfo):
    reply: bytes | None = None

    def create_port(self) -> QSerialPort:
        return MockPort(self.reply)


@pytest.fixture()
def discovery():
    return Discovery()


@pytest.fixture()
def ready(discovery):
    return Spy(discovery.ready)


def test_darwin(available_ports, darwin, discovery, ready):
    available_ports.extend(
        [
            MockPortInfo("cu.usbmodemMG3500014", ti_vid, lp_pid),
            MockPortInfo("tty.usbmodemMG3500014", ti_vid, lp_pid),
            MockPortInfo(
                "cu.usbmodemMG3500011", ti_vid, lp_pid, reply=get_example_version_reply()
            ),
            MockPortInfo("tty.usbmodemMG3500011", ti_vid, lp_pid),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1


def test_linux(available_ports, linux, discovery, ready):
    available_ports.extend(
        [
            MockPortInfo("ttyACM0", ti_vid, lp_pid, reply=get_example_version_reply()),
            MockPortInfo("ttyACM1", ti_vid, lp_pid),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1


def test_windows(available_ports, win32, discovery, ready):
    available_ports.extend(
        [
            MockPortInfo("COM3", ti_vid, lp_pid),
            MockPortInfo("COM2", ti_vid, lp_pid, reply=get_example_version_reply()),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1


def test_windows_reversed(available_ports, win32, discovery, ready):
    available_ports.extend(
        [
            MockPortInfo("COM3", ti_vid, lp_pid, reply=get_example_version_reply()),
            MockPortInfo("COM2", ti_vid, lp_pid),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1
