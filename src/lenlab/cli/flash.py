import logging

from ..launchpad.bsl import Programmer
from ..loop import Loop

logger = logging.getLogger(__name__)


def flash():
    programmer = Programmer()
    programmer.message.connect(logger.info)
    programmer.error.connect(logger.error)
    programmer.program()

    loop = Loop()
    event = loop.run_until(programmer.success, programmer.error, timeout=800)
    assert event, ">= 1 BSL did not emit"
