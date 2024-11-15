import pytest
from PySide6.QtCore import QCoreApplication, QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad.launchpad import find_launchpad


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


@pytest.fixture(scope="session")
def firmware(request):
    if not request.config.getoption("fw"):
        pytest.skip("no firmware")


@pytest.fixture(scope="session")
def bsl(request):
    if not request.config.getoption("bsl"):
        pytest.skip("no BSL")


@pytest.fixture(scope="session", autouse=True)
def app():
    return QCoreApplication()


@pytest.fixture(scope="session")
def port_infos():
    return QSerialPortInfo.availablePorts()


@pytest.fixture(scope="module")
def port(port_infos):
    matches = find_launchpad(port_infos)
    if len(matches) == 0:
        pytest.skip("no launchpad")
    elif len(matches) > 1:
        pytest.skip("too many launchpads")

    port = QSerialPort(matches[0])
    if not port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
        pytest.skip(port.errorString())

    port.clear()
    port.setBaudRate(1_000_000)

    yield port
    port.close()
