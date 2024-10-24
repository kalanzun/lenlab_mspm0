import logging
import platform
import pprint

from PySide6.QtCore import QIODeviceBase, QSysInfo, QEventLoop
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtTest import QSignalSpy

import pytest

from lenlab.singleshot import SingleShotTimer

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


def query(obj, keys):
    for key in keys:
        yield key, getattr(obj, key)()


def pretty(obj):
    return pprint.pformat(obj, sort_dicts=False)


@pytest.mark.sys_info
def test_sys_info():
    logger.info(f"platform(\n{pretty(dict(query(platform, platform_keys)))})")
    logger.info(f"QSysInfo(\n{pretty(dict(query(QSysInfo, sys_info_keys)))})")

    for port_info in QSerialPortInfo.availablePorts():
        if (
        port_info.vendorIdentifier() == 0x0451
        and port_info.productIdentifier() == 0xBEF3):

            logger.info(
                f"QSerialPortInfo(vid=0x0451, pid=0xBEF3,\n{pretty(dict(query(port_info, port_info_keys)))})"
            )

            port = QSerialPort(port_info)
            if port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
                logger.info(f"QSerialPort(\n{pretty(dict(query(port, port_keys)))})")
                port.close()
            else:
                logger.info(port.errorString())
        else:
            logger.debug(
                f"QSerialPortInfo({port_info.portName()})"
            )


class Spy(QSignalSpy):
    def __init__(self, signal):
        super().__init__(signal)

        self._signal = signal

    def event(self, timeout=100):
        if self.count():
            return self.count()

        loop = QEventLoop()
        self._signal.connect(loop.quit)
        timer = SingleShotTimer(loop.quit, timeout)

        timer.start()
        loop.exec()
        self._signal.disconnect(loop.quit)

        return self.count()


@pytest.mark.sys_info
def test_probe():
    port_infos = QSerialPortInfo.availablePorts()

    matches = [
        port_info
        for port_info in port_infos
        if (
            port_info.vendorIdentifier() == 0x0451
            and port_info.productIdentifier() == 0xBEF3
            and port_info.description() == "XDS110 Class Application/User UART"
        )
    ]
    logger.info(f"description matches: {len(matches)}")

    matches = [
        port_info
        for port_info in port_infos
        if (
            port_info.vendorIdentifier() == 0x0451
            and port_info.productIdentifier() == 0xBEF3
        )
    ]
    logger.info(f"vid and pid matches: {len(matches)}")

    for port_info in matches:
        port = QSerialPort(port_info)
        logger.info(f"open {port_info.portName()}")
        if port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            logger.info("send connect packet")
            spy = Spy(port.readyRead)
            port.write(bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE)))
            if spy.event():
                reply = port.readAll().data()
                logger.info(f"reply received {reply}")
                if reply == b"Lk\x00\x00nock":
                    logger.info("firmware found")
                elif reply == b"\x00" or reply == b"\x00\x08\x02\x00;\x06\r\xa7":
                    logger.info("BSL found")
                else:
                    logger.info("unknown reply")
            else:
                logger.info("no reply received")
            port.close()
        else:
            logger.info(port.errorString())
