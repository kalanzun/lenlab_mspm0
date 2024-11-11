import logging
from importlib import resources

from PySide6.QtCore import QCoreApplication
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

import lenlab

from . import cli
from .bsl import BootstrapLoader, Programmer
from .launchpad import find_vid_pid
from .spy import Spy
from .terminal import Terminal

logger = logging.getLogger(__name__)


@cli.command
def flash(args):
    firmware_bin = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

    app = QCoreApplication()  # noqa: F841

    port_infos = find_vid_pid(QSerialPortInfo.availablePorts())
    if not port_infos:
        logger.error("No Launchpad found")
        return 1

    programmer = Programmer([BootstrapLoader(Terminal(QSerialPort(port_info))) for port_info in port_infos])
    programmer.message.connect(logger.info)
    spy = Spy(programmer.finished)
    programmer.program(firmware_bin)
    no_timeout = spy.run_until(600)
    assert no_timeout, "At least one BootstrapLoader did not finish"

    if spy.get_single_arg():
        logger.info("Programming successful")
        return 0

    logger.error("Programming failed")
    return 1
