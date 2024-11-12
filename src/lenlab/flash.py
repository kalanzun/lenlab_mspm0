import logging
from importlib import resources

from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

import lenlab

from .bsl import BootstrapLoader, Programmer
from .launchpad import find_vid_pid
from .loop import loop_until
from .terminal import Terminal

logger = logging.getLogger(__name__)


def flash():
    firmware_bin = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

    port_infos = find_vid_pid(QSerialPortInfo.availablePorts())
    if not port_infos:
        logger.error("No Launchpad found")
        return 1

    programmer = Programmer([BootstrapLoader(Terminal(QSerialPort(port_info))) for port_info in port_infos])
    programmer.message.connect(logger.info)
    programmer.error.connect(logger.error)

    programmer.program(firmware_bin)
    no_timeout = loop_until(programmer.success, programmer.error, timeout=600)
    assert no_timeout, "at least one bootstrap loader did neither emit an error nor the success signal"
