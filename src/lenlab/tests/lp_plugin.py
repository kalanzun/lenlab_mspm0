from dataclasses import dataclass

import pytest
from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad import find_launchpad


def pytest_addoption(parser):
    # pytest_addoption requires a plugin
    # pytest imports conftest within a package only after cli parsing
    parser.addoption(
        "--port",
        action="store",
        help="launchpad serial port name",
    )
    parser.addoption(
        "--fw",
        action="store_true",
        default=False,
        help="assume launchpad with firmware",
    )
    parser.addoption(
        "--bsl",
        action="store_true",
        default=False,
        help="assume launchpad with BSL",
    )


@pytest.fixture(scope="session")
def port_infos() -> list[QSerialPortInfo]:
    return QSerialPortInfo.availablePorts()


@dataclass(slots=True)
class Launchpad:
    port_info: QSerialPortInfo | None = None
    firmware: bool = False
    bsl: bool = False


@pytest.fixture(scope="session")
def launchpad(request, port_infos: list[QSerialPortInfo]) -> Launchpad:
    if port_name := request.config.getoption("--port"):
        matches = [port_info for port_info in port_infos if port_info.portName() == port_name]
    else:
        matches = find_launchpad(port_infos)
        if len(matches) > 1:
            pytest.skip("cannot choose port")

    if not matches:
        pytest.skip("no port found")

    return Launchpad(
        matches[0],
        firmware=request.config.getoption("--fw"),
        bsl=request.config.getoption("--bsl"),
    )


@pytest.fixture(scope="session")
def firmware(launchpad: Launchpad) -> Launchpad:
    if launchpad.firmware:
        return launchpad

    pytest.skip("no firmware found")


@pytest.fixture(scope="session")
def bsl(launchpad: Launchpad) -> Launchpad:
    if launchpad.bsl:
        return launchpad

    pytest.skip("no BSL found")


@pytest.fixture(scope="module")
def port(launchpad: Launchpad) -> QSerialPort:
    port = QSerialPort(launchpad.port_info)
    if not port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
        pytest.skip(port.errorString())

    if launchpad.firmware:
        port.setBaudRate(1_000_000)

    port.clear()  # The OS may have leftovers in the buffers
    yield port
    port.close()
