from logging import getLogger

from PySide6.QtSerialPort import QSerialPort

from lenlab.bsl import BootstrapLoader
from lenlab.protocol import Protocol

logger = getLogger(__name__)


def test_resilience_to_false_baudrate(bsl, port: QSerialPort):
    # send the knock packet at 1 MBaud
    port.setBaudRate(Protocol.baud_rate)
    port.write(Protocol.knock_packet)
    assert not port.waitForReadyRead(100), "BSL should not reply"

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(BootstrapLoader.baud_rate)
    port.write(BootstrapLoader.connect_packet)
    assert port.waitForReadyRead(100), "BSL should reply"

    # assume cold BSL
    reply = port.readAll().data()
    assert reply == b"\x00"
