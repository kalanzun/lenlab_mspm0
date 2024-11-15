import logging
from importlib import resources

from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

import lenlab

from ..launchpad.bsl import BootstrapLoader, Programmer
from ..launchpad.launchpad import find_vid_pid
from ..launchpad.terminal import Terminal
from ..loop import Loop

logger = logging.getLogger(__name__)


def flash():
    firmware_bin = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

    port_infos = QSerialPortInfo.availablePorts()
    matches = find_vid_pid(port_infos)  # let's test discovery and give all launchpad ports
    if not matches:
        logger.error("No Launchpad found")
        return

    programmer = Programmer([BootstrapLoader(Terminal(QSerialPort(port_info))) for port_info in matches])
    programmer.message.connect(logger.info)
    programmer.error.connect(logger.error)

    programmer.program(firmware_bin)
    loop = Loop()
    event = loop.run_until(programmer.success, programmer.error, timeout=800)
    assert event, "At least one bootstrap loader did neither emit an error nor the success signal"
