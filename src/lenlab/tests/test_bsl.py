from PySide6.QtSerialPort import QSerialPort


def test_resilience_to_false_baudrate(bsl, port: QSerialPort):
    # cold or warm bsl

    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(bsl.knock_packet)
    assert not port.waitForReadyRead(100), "bsl should not reply"

    # send the bsl connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(bsl.connect_packet)
    assert port.waitForReadyRead(100), "bsl should reply"

    # the reply is a single 0 or the ok_packet
    n = port.bytesAvailable()
    if n == 1:
        reply = port.readAll().data()
        assert reply == b"\x00"
        assert not port.waitForReadyRead(100), "spurious data"

    else:
        while port.bytesAvailable() < 10:
            assert port.waitForReadyRead(100)

        reply = port.readAll().data()
        assert reply == bsl.ok_packet


def test_invalid_head(bsl, port: QSerialPort):
    # assume warm bsl
    port.write(b"Q")  # anything but 0x80
    assert port.waitForReadyRead(100)
    assert port.bytesAvailable() == 1
    assert port.read(1).data() == b"Q"


def test_zero_length(bsl, port: QSerialPort):
    # assume warm bsl
    port.write(b"\x80\x00\x00")
    assert port.waitForReadyRead(100)
    assert port.bytesAvailable() == 1
    assert port.read(1).data() == b"S"
