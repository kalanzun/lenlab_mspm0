from PySide6.QtSerialPort import QSerialPort

from lenlab.bsl import BootstrapLoader
from lenlab.protocol import Protocol


def test_resilience_to_false_baudrate(firmware, port: QSerialPort):
    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(BootstrapLoader.baud_rate)
    port.write(BootstrapLoader.connect_packet)
    assert not port.waitForReadyRead(100), "Firmware should not reply"

    # send the knock packet at 1 MBaud
    port.setBaudRate(Protocol.baud_rate)
    port.write(Protocol.knock_packet)
    assert port.waitForReadyRead(100), "Firmware should reply"

    reply = port.readAll().data()
    assert reply == Protocol.knock_packet
