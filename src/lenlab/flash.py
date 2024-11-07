import logging
from importlib import resources

from PySide6.QtCore import QCoreApplication
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

import lenlab

from . import cli
from .bsl import BootstrapLoader, BSLDiscovery
from .launchpad import find_vid_pid
from .spy import Spy
from .terminal import Terminal

logger = logging.getLogger(__name__)


@cli.command
def flash(args):
    firmware_bin = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

    app = QCoreApplication()  # noqa: F841

    terminals = list()
    for port_info in find_vid_pid(QSerialPortInfo.availablePorts()):
        port = QSerialPort(port_info)
        terminals.append(Terminal(port))

    discovery = BSLDiscovery(terminals)
    loader = BootstrapLoader(discovery)

    loader.message.connect(logger.info)
    spy = Spy(loader.finished)
    loader.program(firmware_bin)
    spy.run_until_single_arg(500)
