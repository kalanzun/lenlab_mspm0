from collections.abc import Generator
from contextlib import closing
from dataclasses import dataclass
from logging import getLogger
from typing import Self

import pytest
from PySide6.QtCore import QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad import connect_packet, find_launchpad, knock_packet, ok_packet

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


class LaunchpadError(Exception):
    pass


@dataclass(slots=True, frozen=True)
class Launchpad:
    port_info: QSerialPortInfo
    baud_rate: int = 1_000_000
    firmware: bool = False
    bsl: bool = False

    @property
    def port_name(self) -> str:
        return self.port_info.portName()

    def open_port(self) -> QSerialPort:
        port = QSerialPort(self.port_info)
        if not port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            raise LaunchpadError(port.errorString())

        port.setBaudRate(self.baud_rate)
        port.clear()  # The OS may have leftovers in the buffers
        return port

    @classmethod
    def discover(cls, port_infos: list[QSerialPortInfo]) -> Generator[Self]:
        for port_info in port_infos:
            launchpad = None
            with closing(cls(port_info).open_port()) as port:
                # port.setBaudRate(1_000_000)
                port.write(knock_packet)
                if port.waitForReadyRead(100):
                    reply = port.readAll().data()
                    if reply and knock_packet.startswith(reply):
                        launchpad = cls(QSerialPortInfo(port), firmware=True)
                        logger.info(f"{launchpad.port_name}: firmware found")
                        yield launchpad

                port.setBaudRate(9_600)
                port.write(connect_packet)
                if port.waitForReadyRead(100):
                    reply = port.readAll().data()
                    if reply and ok_packet.startswith(reply):
                        launchpad = cls(QSerialPortInfo(port), baud_rate=9_600, bsl=True)
                        logger.info(f"{launchpad.port_name}: BSL found")
                        yield launchpad

            if not launchpad:
                logger.info(f"{port_info.portName()}: nothing found")


@pytest.fixture(scope="session")
def launchpad(request, port_infos: list[QSerialPortInfo]) -> Launchpad:
    if port_name := request.config.getoption("port"):
        matches = [port_info for port_info in port_infos if port_info.portName() == port_name]
    else:
        matches = find_launchpad(port_infos)

    if not matches:
        pytest.skip("no port found")

    _firmware = request.config.getoption("fw")
    _bsl = request.config.getoption("bsl")
    if _firmware or _bsl:
        if len(matches) > 1:
            pytest.skip("cannot choose port")

        launchpad = Launchpad(
            matches[0],
            baud_rate=1_000_000 if _firmware else 9_600,
            firmware=_firmware,
            bsl=_bsl,
        )
        return launchpad

    launchpad = next(Launchpad.discover(matches), None)
    if not launchpad:
        pytest.skip("no launchpad found")

    return launchpad


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
    port = launchpad.open_port()
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
