from PySide6.QtSerialPort import QSerialPort

from lenlab import launchpad
from lenlab.lenlab import pack

KB = 1024


def test_knock(firmware, port: QSerialPort):
    port.write(launchpad.knock_packet)
    while port.bytesAvailable() < 8:
        assert port.waitForReadyRead(100), "no reply received"
    reply = port.readAll().data()
    assert reply == launchpad.knock_packet


def test_28kb(firmware, port: QSerialPort):
    port.write(pack(b"m28KB"))
    while port.bytesAvailable() < 28 * KB:
        if not port.waitForReadyRead(300):
            break
    reply = port.readAll().data()
    assert len(reply) == 28 * KB
