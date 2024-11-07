from importlib import resources
from logging import getLogger

from PySide6.QtSerialPort import QSerialPort

import lenlab
from lenlab.bsl import BootstrapLoader
from lenlab.terminal import Terminal
from lenlab.spy import Spy

logger = getLogger(__name__)


def test_resilience_to_false_baudrate(bsl, port: QSerialPort):
    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(bsl.knock_packet)
    assert not port.waitForReadyRead(100), "BSL should not reply"

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(bsl.connect_packet)
    assert port.waitForReadyRead(100), "BSL should reply"

    reply = port.readAll().data()
    assert len(reply), "No reply"
    assert reply[0] == 0, "No success"


def test_flash(flash, port: QSerialPort):
    firmware_bin = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

    terminal = Terminal(port)
    terminal.open()
    loader = BootstrapLoader(terminal)

    loader.message.connect(logger.info)
    spy = Spy(loader.finished)
    loader.program(firmware_bin)
    assert spy.run_until_single_arg(1000), "no success or timeout"
