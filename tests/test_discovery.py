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
    spy = Spy(discovery.result)
    error = Spy(discovery.error)
    discovery.discover()
    if error.count():
        pytest.skip(str(error.get_single_arg()))

    loop = Loop()
    event = loop.run_until(discovery.result, discovery.error, timeout=600)
    assert event, ">= 1 probe did not emit"

    result = spy.get_single_arg()
    if request.config.getoption("fw"):
        assert isinstance(result, Terminal)
        logger.info(f"firmware found on {result.port_name}")
    elif request.config.getoption("bsl"):
        assert result is None
        logger.info("nothing found")
    else:
        if isinstance(result, Terminal):
            logger.info(f"firmware found on {result.port_name}")
        else:
            logger.info("nothing found")
