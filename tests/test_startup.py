import sys
from logging import getLogger

import pytest
from attrs import frozen
from PySide6.QtCore import QByteArray
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad import discovery as discovery_messages
from lenlab.launchpad import linux
from lenlab.launchpad import terminal as terminal_messages
from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.launchpad import lp_pid, ti_vid, tiva_pid
from lenlab.launchpad.port_info import PortInfo
from lenlab.launchpad.protocol import get_example_version_reply
from lenlab.message import Message
from lenlab.spy import Spy

logger = getLogger(__name__)


@pytest.fixture(autouse=True)
def platform_any(monkeypatch):
    monkeypatch.setattr(sys, "platform", "any")


@pytest.fixture()
def platform_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")


@pytest.fixture()
def platform_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(linux, "check_rules", lambda: True)


@pytest.fixture()
def no_rules(monkeypatch):
    monkeypatch.setattr(linux, "check_rules", lambda: False)


@pytest.fixture()
def platform_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")


@pytest.fixture()
def available_ports(monkeypatch):
    available_ports = []
    monkeypatch.setattr(PortInfo, "available_ports", lambda: available_ports)
    return available_ports


class MockPort(QSerialPort):
    def __init__(
        self, reply: bytes | None = None, error: QSerialPort.SerialPortError | None = None
    ):
        super().__init__()

        self.reply = reply
        self.error = error

    def open(self, mode):
        self.errorOccurred.emit(QSerialPort.SerialPortError.NoError)

        if self.error is None:
            return True
        else:
            self.errorOccurred.emit(self.error)
            return False

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
    error: QSerialPort.SerialPortError | None = None

    def create_port(self) -> QSerialPort:
        return MockPort(reply=self.reply, error=self.error)


@pytest.fixture()
def discovery():
    return Discovery()


@pytest.fixture()
def ready(discovery):
    discovery.ready.connect(lambda terminal: logger.info(f"{terminal.port_name} ready"))
    return Spy(discovery.ready)


def log_message(message: Message):
    logger.info(message.long_form())


@pytest.fixture()
def error(discovery):
    discovery.error.connect(log_message)
    return Spy(discovery.error)


def test_darwin(platform_darwin, available_ports, discovery, ready):
    logger.info("Mac, Launchpad ready")
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


def test_linux(platform_linux, available_ports, discovery, ready):
    logger.info("Linux, Launchpad ready")
    available_ports.extend(
        [
            MockPortInfo("ttyACM0", ti_vid, lp_pid, reply=get_example_version_reply()),
            MockPortInfo("ttyACM1", ti_vid, lp_pid),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1


def test_windows(platform_win32, available_ports, discovery, ready):
    logger.info("Windows, Launchpad ready")
    available_ports.extend(
        [
            MockPortInfo("COM3", ti_vid, lp_pid),
            MockPortInfo("COM2", ti_vid, lp_pid, reply=get_example_version_reply()),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1


def test_windows_reversed(platform_win32, available_ports, discovery, ready):
    logger.info("Windows, Launchpad reversed and ready")
    available_ports.extend(
        [
            MockPortInfo("COM3", ti_vid, lp_pid, reply=get_example_version_reply()),
            MockPortInfo("COM2", ti_vid, lp_pid),
        ]
    )

    discovery.find()
    discovery.probe()

    assert ready.count() == 1


def test_no_launchpad(available_ports, discovery, error):
    logger.info("No Launchpad")
    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_messages.NoLaunchpad)


def test_tiva_launchpad(available_ports, discovery, error):
    logger.info("Tiva Launchpad")
    available_ports.extend(
        [
            MockPortInfo("COM1", ti_vid, tiva_pid),
        ]
    )

    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_messages.TivaLaunchpad)


def test_no_rules(platform_linux, no_rules, available_ports, discovery, error):
    logger.info("Linux, No Rules")
    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_messages.NoRules)


def test_not_found(available_ports, discovery, error):
    logger.info("Not Found")

    discovery.port_name = "COM0"
    discovery.find()

    assert isinstance(error.get_single_arg(), discovery_messages.NotFound)


def test_no_permission(available_ports, discovery, error):
    logger.info("No Permission")
    available_ports.extend(
        [
            MockPortInfo(
                "COM1",
                ti_vid,
                lp_pid,
                error=QSerialPort.SerialPortError.PermissionError,
            ),
        ]
    )

    discovery.find()
    discovery.probe()

    assert isinstance(error.get_single_arg(), terminal_messages.NoPermission)


def test_invalid_packet(available_ports, discovery, error):
    logger.info("Invalid Packet")
    available_ports.extend(
        [
            MockPortInfo("COM1", ti_vid, lp_pid, reply=bytearray(8)),
        ]
    )

    discovery.find()
    discovery.probe()

    assert isinstance(error.get_single_arg(), terminal_messages.InvalidPacket)


def test_invalid_version(available_ports, discovery, error):
    logger.info("Invalid Version")
    available_ports.extend(
        [
            MockPortInfo("COM1", ti_vid, lp_pid, reply=b"L8\x00\x000a0\x00"),
        ]
    )

    discovery.find()
    discovery.probe()

    assert isinstance(error.get_single_arg(), discovery_messages.InvalidVersion)


def test_invalid_reply(available_ports, discovery, error):
    logger.info("Invalid Reply")
    available_ports.extend(
        [
            MockPortInfo("COM1", ti_vid, lp_pid, reply=b"L\x00\x00\x00\x00\x00\x00\x00"),
        ]
    )

    discovery.find()
    discovery.probe()

    assert isinstance(error.get_single_arg(), discovery_messages.InvalidReply)


def test_no_firmware(available_ports, discovery, error):
    logger.info("No Firmware")
    available_ports.extend(
        [
            MockPortInfo("COM1", ti_vid, lp_pid),
        ]
    )

    discovery.find()
    discovery.probe()

    discovery.timer.timeout.emit()

    assert isinstance(error.get_single_arg(), discovery_messages.NoFirmware)
