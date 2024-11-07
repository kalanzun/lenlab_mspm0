import logging
import platform
import pprint
from contextlib import closing

from PySide6.QtCore import QIODeviceBase, QSysInfo
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from . import cli
from . import launchpad

logger = logging.getLogger(__name__)

platform_keys = [
    "architecture",
    "machine",
    "platform",
    "processor",
    "system",
    "version",
    "uname",
]

sys_info_keys = [
    "buildAbi",
    "buildCpuArchitecture",
    "currentCpuArchitecture",
    "kernelType",
    "kernelVersion",
    "prettyProductName",
    "productType",
    "productVersion",
]

port_info_keys = [
    "description",
    "manufacturer",
    "portName",
    "productIdentifier",
    "vendorIdentifier",
    "serialNumber",
    "systemLocation",
]

port_keys = [
    "baudRate",
    "dataBits",
    "errorString",
    "flowControl",
    "parity",
    "stopBits",
    # "isBreakEnabled",
    # "isDataTerminalReady",
    # "isRequestToSend",
]


def pretty(obj: object, keys: list[str]) -> str:
    info = {key: getattr(obj, key)() for key in keys}
    return pprint.pformat(info, sort_dicts=False, underscore_numbers=True)


@cli.command
def sys_info(args):
    logging.basicConfig(level=logging.INFO)

    port_infos = QSerialPortInfo.availablePorts()
    logger.info(f"platform\n{pretty(platform, platform_keys)}")
    logger.info(f"QSysInfo\n{pretty(QSysInfo, sys_info_keys)}")

    for port_info in port_infos:
        if port_info.vendorIdentifier() == launchpad.ti_vid and port_info.productIdentifier() == launchpad.ti_pid:
            description = " description matches" if port_info.description() == launchpad.port_description else ""
            logger.info(f"QSerialPortInfo Launchpad{description}\n{pretty(port_info, port_info_keys)}")

            port = QSerialPort(port_info)
            if port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
                with closing(port):
                    logger.info(f"QSerialPort {port_info.portName()}\n{pretty(port, port_keys)}")
            else:
                logger.info(port.errorString())
        else:
            logger.info(f"QSerialPortInfo {port_info.portName()}")
