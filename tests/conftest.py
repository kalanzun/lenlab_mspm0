import pytest
from PySide6.QtCore import QCoreApplication, QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad import find_launchpad
from lenlab.protocol import Protocol


@pytest.fixture(scope="session", autouse=True)
def app() -> QCoreApplication:
    return QCoreApplication()


@pytest.fixture(scope="session")
def port_infos() -> list[QSerialPortInfo]:
    return QSerialPortInfo.availablePorts()


def pytest_addoption(parser):
    parser.addoption(
        "--fw",
        action="store_true",
        default=False,
        help="run firmware tests",
    )
    parser.addoption(
        "--bsl",
        action="store_true",
        default=False,
        help="run BSL tests",
    )


@pytest.fixture(scope="module")
def firmware(request) -> None:
    if not request.config.getoption("fw"):
        pytest.skip("no firmware")


@pytest.fixture(scope="module")
def bsl(request, port: QSerialPort) -> None:
    if not request.config.getoption("bsl"):
        pytest.skip("no BSL")


@pytest.fixture(scope="module")
def port(request, port_infos: list[QSerialPortInfo]) -> QSerialPort:
    matches = find_launchpad(port_infos)
    if len(matches) == 0:
        pytest.skip("no port")
    elif len(matches) > 1:
        pytest.skip("too many ports")

    port = QSerialPort(matches[0])
    assert port.open(QIODeviceBase.OpenModeFlag.ReadWrite), port.errorString()

    if request.config.getoption("fw"):
        port.setBaudRate(Protocol.baud_rate)

    yield port
    port.close()
