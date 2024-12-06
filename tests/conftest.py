import pytest
from PySide6.QtCore import QIODeviceBase, QCoreApplication
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QApplication

from lenlab.launchpad.launchpad import find_launchpad
from lenlab.launchpad.terminal import Terminal


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
    parser.addoption(
        "--port",
        help="launchpad port name",
    )
    parser.addoption(
        "--gui",
        action="store_true",
        default=False,
        help="enable gui tests",
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
def app(request):
    if request.config.getoption("gui"):
        # support view tests with QtWidgets
        return QApplication()
    else:
        return QCoreApplication()


@pytest.fixture(scope="session")
def gui(request):
    if not request.config.getoption("gui"):
        pytest.skip("no gui")


@pytest.fixture(scope="session")
def port_infos():
    return QSerialPortInfo.availablePorts()


@pytest.fixture(scope="module")
def port(request, port_infos):
    if port_name := request.config.getoption("port"):
        port_info = QSerialPortInfo(port_name)

    else:
        matches = find_launchpad(port_infos)
        if len(matches) == 0:
            pytest.skip("no launchpad")
        elif len(matches) > 1:
            pytest.skip("too many launchpads")
        port_info = matches[0]

    port = QSerialPort(port_info)
    if not port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
        pytest.skip(port.errorString())

    port.clear()
    port.setBaudRate(1_000_000)

    yield port
    port.close()


@pytest.fixture(scope="module")
def terminal(port: QSerialPort) -> Terminal:
    terminal = Terminal(port)
    # port is already open, but open() also connects the signal handlers
    terminal.open()
    yield terminal
    terminal.close()
