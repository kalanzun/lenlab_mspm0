from logging import getLogger

import pytest
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.discovery import Discovery, Probe
from lenlab.launchpad import find_vid_pid
from lenlab.loop import loop_until
from lenlab.spy import Spy
from lenlab.terminal import Terminal

logger = getLogger(__name__)


def test_discovery(request, port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no launchpad")

    discovery = Discovery([Probe(Terminal(QSerialPort(port_info))) for port_info in matches])
    discovery.message.connect(logger.info)
    spy = Spy(discovery.result)
    discovery.start()
    no_timeout = loop_until(discovery.result, discovery.error, timeout=600)
    assert no_timeout, "at least one probe did neither emit an error nor the success signal"

    terminal = spy.get_single_arg()
    if request.config.getoption("fw"):
        assert isinstance(terminal, Terminal)
        logger.info("firmware found")
    elif request.config.getoption("bsl"):
        assert terminal is None
        logger.info("nothing found")
