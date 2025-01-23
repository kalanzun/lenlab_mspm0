import pytest

from lenlab.app.status import FirmwareStatus, LaunchpadStatus, StatusMessage
from lenlab.device.device import Device
from lenlab.device.lenlab import Lenlab
from lenlab.launchpad.terminal import FirmwareError, LaunchpadError


@pytest.fixture()
def status_message(monkeypatch):
    monkeypatch.setattr(StatusMessage, "show", lambda self: None)
    return StatusMessage(Lenlab())


def test_ready(status_message):
    status_message.on_ready()


def test_no_launchpad(status_message):
    status_message.on_error(LaunchpadError())


def test_no_firmware(status_message):
    status_message.on_error(FirmwareError())


def test_button(status_message):
    status_message.on_button_clicked()


@pytest.fixture()
def launchpad_status():
    return LaunchpadStatus(Device(Lenlab()))


def test_launchpad_status_available(launchpad_status):
    launchpad_status.on_available()


def test_launchpad_status_error(launchpad_status):
    launchpad_status.on_error(LaunchpadError())


@pytest.fixture()
def firmware_status():
    return FirmwareStatus(Device(Lenlab()))


def test_firmware_status_available(firmware_status):
    firmware_status.on_available()


def test_firmware_status_ready(firmware_status):
    firmware_status.on_ready()


def test_firmware_status_launchpad_error(firmware_status):
    firmware_status.on_error(LaunchpadError())


def test_firmware_status_firmware_error(firmware_status):
    firmware_status.on_error(FirmwareError())
