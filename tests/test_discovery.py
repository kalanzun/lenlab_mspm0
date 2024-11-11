from logging import getLogger

import pytest
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.discovery import Discovery, Probe
from lenlab.launchpad import find_vid_pid
from lenlab.spy import Spy
from lenlab.terminal import Terminal

logger = getLogger(__name__)


def test_discovery(request, port_infos: list[QSerialPortInfo]):
    matches = find_vid_pid(port_infos)
    if not matches:
        pytest.skip("no launchpad found")

    discovery = Discovery([Probe(Terminal(QSerialPort(port_info))) for port_info in matches])
    discovery.message.connect(logger.info)
    spy = Spy(discovery.result)
    discovery.start()
    no_timeout = spy.run_until(600)
    assert no_timeout, "at least one probe did not finish"

    result = spy.get_single_arg()
    if request.config.getoption("fw"):
        assert isinstance(result, Terminal)
    elif request.config.getoption("bsl"):
        assert result is None
    else:
        assert isinstance(result, Terminal) or result is None
        if result is None:
            logger.info("nothing found")
        else:
            logger.info("firmware found")
