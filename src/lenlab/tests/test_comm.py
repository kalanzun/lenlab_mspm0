from PySide6.QtSerialPort import QSerialPort

from lenlab import launchpad


def test_knock(firmware, port: QSerialPort):
    port.write(launchpad.knock_packet)
    while port.bytesAvailable() < 8:
        assert port.waitForReadyRead(100), "no reply received"
    reply = port.readAll().data()
    assert reply == launchpad.knock_packet
