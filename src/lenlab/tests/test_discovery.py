from contextlib import closing
from logging import getLogger

import pytest
from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.launchpad import connect_packet, find_vid_pid, knock_packet, ok_packet
from lenlab.tests.lp_plugin import Launchpad

logger = getLogger(__name__)


def test_all_discovery(port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no port found")

    result = list(Launchpad.discover(matches))
    if not result:
        pytest.skip("no launchpad found")

    assert len(result) == 1


def test_single_discovery(port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no port found")

    result = next(Launchpad.discover(matches), None)
    if not result:
        pytest.skip("no launchpad found")


def test_firmware_responsive(firmware: Launchpad):
    # previous tests have run discovery
    with closing(firmware.open_port()) as port:
        port.write(knock_packet)
        while port.bytesAvailable() < len(knock_packet):
            assert port.waitForReadyRead(100)
        reply = port.readAll().data()
        assert reply == knock_packet
        logger.info(f"{firmware.port_name}: firmware responsive")


def test_bsl_responsive(bsl: Launchpad):
    # previous tests have run discovery
    with closing(bsl.open_port()) as port:
        port.write(connect_packet)
        while port.bytesAvailable() < len(ok_packet):
            assert port.waitForReadyRead(100)
        reply = port.readAll().data()
        assert reply == ok_packet
        logger.info(f"{bsl.port_name}: BSL responsive")