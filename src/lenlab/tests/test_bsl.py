from importlib import resources
from logging import getLogger

from PySide6.QtSerialPort import QSerialPort

from lenlab.bsl import BootstrapLoader
from lenlab.terminal import Terminal
from lenlab.tests.spy import Spy

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

    # the reply is either a single 0 or the first bytes of the ok_packet
    reply = port.readAll().data()
    assert len(reply)
    assert bsl.ok_packet.startswith(reply), "Reply is not the first bytes of the ok packet"


def test_flash(flash, port: QSerialPort):
    import lenlab

    firmware_bin = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

    terminal = Terminal(port)
    loader = BootstrapLoader(terminal)

    loader.message.connect(logger.info)
    spy = Spy(loader.finished)
    loader.program(firmware_bin)
    assert spy.run_until(1000)
