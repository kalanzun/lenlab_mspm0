from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtSerialPort import QSerialPort


def packet(cmd: bytes):
    assert len(cmd) == 5
    return b"L\x01\x00" + cmd


class Terminal(QObject):
    reply = Signal(bytes)
    bsl_ack = Signal(bytes)
    bsl_reply = Signal(bytes)

    def __init__(self, port: QSerialPort):
        super().__init__()
        self.port = port
        self.port.readyRead.connect(self.on_ready_read)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.on_timeout)

    @Slot()
    def on_ready_read(self):
        n = self.port.bytesAvailable()
        if n >= 1:
            ack = self.port.peek(1).data()
            if ack in b"\x00QRSTUV":  # 0x51 - 0x56
                ack = self.port.read(1).data()
                n -= len(ack)
                self.bsl_ack.emit(ack)

        if n >= 7:
            head = self.port.peek(3).data()
            if head[0] in b"\x08L":
                length = int.from_bytes(head[1:3], byteorder="little") + 7
                if n >= length:
                    reply = self.port.read(length).data()
                    n -= len(reply)
                    if reply[0] == 8:
                        self.bsl_reply.emit(reply)
                    else:
                        self.reply.emit(reply)

        if n == 0:
            self.timer.stop()
        else:
            self.timer.start()

    @Slot()
    def on_timeout(self) -> None:
        self.port.readAll()


class SyncTerminal:
    def __init__(self, port: QSerialPort):
        self.port = port

    def wait_for_packet(self, length: int = 8, timeout: int = 200) -> bool:
        while self.port.bytesAvailable() < length:
            if not self.port.waitForReadyRead(timeout):
                self.port.readAll()  # clear out partial packet data
                return False  # timeout

        return True  # length bytes available

    def read(self) -> bytes:
        # do read extra data
        return self.port.readAll().data()

    def read_packet(self, length: int = 8, timeout: int = 200) -> bytes | None:
        if self.wait_for_packet(length, timeout):
            return self.read()

    def write(self, data: bytes):
        self.port.write(data)

    def wait_for_transmission(self, timeout: int = 200) -> bool:
        return self.port.waitForBytesWritten(timeout)
