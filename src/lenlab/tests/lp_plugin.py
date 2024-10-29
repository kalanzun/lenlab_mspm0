from dataclasses import dataclass
from logging import getLogger

import pytest
from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad import find_launchpad
from lenlab.terminal import Terminal

logger = getLogger(__name__)


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


phase_report_key = pytest.StashKey[dict[str, pytest.CollectReport]]()


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    rep = yield

    # store test results for each phase of a call, which can
    # be "setup", "call", "teardown"
    item.stash.setdefault(phase_report_key, {})[rep.when] = rep

    return rep


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


@pytest.fixture
def cleanup(request, port: QSerialPort):
    yield

    report = request.node.stash[phase_report_key]
    if "call" in report and report["call"].failed:
        logger.info("cleanup")
        while port.waitForReadyRead(300):  # wait for timeout
            pass

        if port.bytesAvailable():
            logger.warning("spurious bytes cleaned up")

        port.clear()


@pytest.fixture(scope="module")
def terminal(port: QSerialPort) -> Terminal:
    terminal = Terminal(port)
    # port is already open
    yield terminal
    terminal.close()
