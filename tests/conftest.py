import pytest
from PySide6.QtCore import QCoreApplication, QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad import port_description


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


@pytest.fixture(scope="session")
def port_info(port_infos):
    for port_info in port_infos:
        if port_info.description() == port_description:
            return port_info

    pytest.skip("no port")


@pytest.fixture(scope="session")
def port(port_info):
    port = QSerialPort(port_info)
    if not port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
        pytest.skip(port.errorString())

    port.clear()
    port.setBaudRate(1_000_000)

    yield port
    port.close()


@pytest.fixture(scope="session")
def send(port):
    def send(command: bytes):
        port.write(command)

    return send


@pytest.fixture(scope="session")
def receive(port):
    def receive(n: int, timeout: int = 100) -> bytes:
        while port.bytesAvailable() < n:
            if not port.waitForReadyRead(timeout):
                raise TimeoutError(f"{port.bytesAvailable()} bytes of {n} bytes received")
        return port.read(n).data()

    return receive
