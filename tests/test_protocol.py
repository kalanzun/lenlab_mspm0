from PySide6.QtSerialPort import QSerialPort

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
knock_packet = b"Lk\x00\x00nock"


def test_bsl_resilience_to_false_baud_rate(bsl, port: QSerialPort):
    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert not port.waitForReadyRead(100), "BSL should not reply"

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert port.waitForReadyRead(100), "BSL should reply"

    # assume cold BSL
    # warm BSL for further tests
    reply = port.readAll().data()
    assert reply == b"\x00"


def test_firmware_resilience_to_false_baud_rate(firmware, port: QSerialPort):
    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert not port.waitForReadyRead(100), "Firmware should not reply"

    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert port.waitForReadyRead(100), "Firmware should reply"

    reply = port.readAll().data()
    assert reply == knock_packet


def test_knock(firmware, send, receive):
    send(knock_packet)
    reply = receive(len(knock_packet))
    assert reply == knock_packet
