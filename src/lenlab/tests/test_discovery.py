from contextlib import closing
from logging import getLogger

import pytest
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.discovery import Discovery, Future
from lenlab.launchpad import find_vid_pid
from lenlab.terminal import Terminal
from lenlab.tests.spy import Spy

logger = getLogger(__name__)


def test_all_launchpad_discovery(launchpad, port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no port found")

    result = list(launchpad.discover(matches))
    if not result:
        pytest.skip("no launchpad found")

    assert len(result) == 1


def test_single_launchpad_discovery(launchpad, port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no port found")

    result = next(launchpad.discover(matches), None)
    if not result:
        pytest.skip("no launchpad found")


def test_firmware_responsive(firmware):
    # previous tests have run discovery
    with closing(firmware.open_port()) as port:
        port.write(firmware.knock_packet)
        while port.bytesAvailable() < len(firmware.knock_packet):
            assert port.waitForReadyRead(100)
        reply = port.readAll().data()
        assert reply == firmware.knock_packet
        logger.info(f"{firmware.port_name}: firmware responsive")


def test_bsl_responsive(bsl):
    # previous tests have run discovery
    with closing(bsl.open_port()) as port:
        port.write(bsl.connect_packet)
        while port.bytesAvailable() < len(bsl.ok_packet):
            assert port.waitForReadyRead(100)
        reply = port.readAll().data()
        assert reply == bsl.ok_packet
        logger.info(f"{bsl.port_name}: bsl responsive")


def test_discovery(port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no port found")

    future = Future()
    future.error.connect(logger.info)
    spy = Spy(future.result)

    for match in matches:
        port = QSerialPort(match)
        terminal = Terminal(port)
        discovery = Discovery(terminal)
        discovery.error.connect(future.error.emit)
        discovery.result.connect(future.result.emit)
        discovery.start()

    if not spy.run_until(800):
        pytest.skip("no launchpad found")

    terminal = spy.get_single_arg()
    assert terminal

    if terminal.firmware:
        logger.info(f"{terminal.port_name}: firmware found")

    if terminal.bsl:
        logger.info(f"{terminal.port_name}: bsl found")
