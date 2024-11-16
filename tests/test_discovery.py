from logging import getLogger

import pytest
from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.terminal import Terminal
from lenlab.loop import Loop
from lenlab.spy import Spy

logger = getLogger(__name__)


def test_discovery(request, port_infos: list[QSerialPortInfo]):
    discovery = Discovery()
    discovery.message.connect(logger.info)
    spy = Spy(discovery.result)
    error = Spy(discovery.error)
    discovery.discover()
    if error.count():
        pytest.skip(str(error.get_single_arg()))

    loop = Loop()
    event = loop.run_until(discovery.result, discovery.error, timeout=600)
    assert event, "at least one probe did neither emit an error nor the success signal"

    terminal = spy.get_single_arg()
    if request.config.getoption("fw"):
        assert isinstance(terminal, Terminal)
        logger.info(f"firmware found on {terminal.port_name}")
    elif request.config.getoption("bsl"):
        assert terminal is None
        logger.info("nothing found")
    else:
        if isinstance(terminal, Terminal):
            logger.info(f"firmware found on {terminal.port_name}")
        else:
            logger.info("nothing found")
