from PySide6.QtSerialPort import QSerialPort


def test_resilience_to_false_baudrate(firmware, port: QSerialPort):
    # send the bsl connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(firmware.connect_packet)
    assert not port.waitForReadyRead(100), "Firmware should not reply"

    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(firmware.knock_packet)
    assert port.waitForReadyRead(100), "Firmware should reply"

    # the reply is the first bytes of the knock_packet
    reply = port.readAll().data()
    assert len(reply)
    assert firmware.knock_packet.startswith(reply), "Reply is not the first bytes of the knock packet"
