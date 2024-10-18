import pytest

from typing import Iterable

from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


def find_vid_pid(vid: int, pid: int) -> Iterable[QSerialPortInfo]:
    for port_info in QSerialPortInfo.availablePorts():
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid:
            yield port_info


def connect() -> QSerialPort | None:
    port_infos = list(find_vid_pid(0x0451, 0xBEF3))
    assert len(port_infos) == 2

    aux_port_info, port_info = port_infos
    port = QSerialPort(port_info)
    port.setBaudRate(9600)

    assert port.open(QIODeviceBase.OpenModeFlag.ReadWrite)
    return port


@pytest.fixture
def port() -> QSerialPort | None:
    try:
        return connect()
    except AssertionError:
        pytest.skip("launchpad required")


def probe(port: QSerialPort) -> str:
    port.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    if not port.waitForReadyRead(200):
        return "no response"

    reply = port.readAll().data()
    if reply == b"L\x01\x00hello":
        return "firmware"
    elif reply == b"\x00" or reply == b"\x00\x08\x02\x00;\x06\r\xa7":
        return "bsl"

    return "invalid response"


@pytest.fixture(scope="session")
def launchpad() -> str:
    try:
        port = connect()
    except AssertionError:
        return "no launchpad"

    result = probe(port)
    port.close()
    del port

    return result


@pytest.fixture
def bsl(launchpad: str) -> None:
    if launchpad != "bsl":
        pytest.skip("bsl required")


@pytest.fixture
def firmware(launchpad: str) -> None:
    if launchpad != "firmware":
        pytest.skip("firmware required")


@pytest.fixture
def blank(launchpad: str) -> None:
    if launchpad != "blank":
        pytest.skip("blank flash required")
