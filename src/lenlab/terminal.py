from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort


class Terminal(QObject):
    ack = Signal()
    error = Signal(str)
    reply = Signal(bytes)

    def __init__(self, port: QSerialPort | None = None):
        super().__init__()
        self.port = port

        self.firmware = False
        self.bsl = False
        self.ack_mode = False

    @property
    def port_name(self) -> str:
        return self.port.portName()

    @property
    def bytes_available(self) -> int:
        return self.port.bytesAvailable()

    def set_baud_rate(self, baud_rate: int):
        self.port.setBaudRate(baud_rate)

    def open(self) -> bool:
        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

        # testing might have put in an open port
        if self.port.isOpen():
            return True

        # port.open emits a NoError on errorOccurred in any case
        # in case of an error, it emits errorOccurred a second time with the error
        # on_error_occurred handles the error case
        return self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

    def close(self) -> None:
        if self.port.isOpen():
            self.port.close()

    def peek(self, n: int) -> bytes:
        return self.port.peek(n).data()

    def read(self, n: int) -> bytes:
        return self.port.read(n).data()

    def write(self, packet: bytes) -> int:
        return self.port.write(packet)

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error: QSerialPort.SerialPortError) -> None:
        if error is QSerialPort.SerialPortError.NoError:
            pass
        else:
            self.error.emit(self.port.errorString())

    @Slot()
    def on_ready_read(self) -> None:
        n = self.bytes_available
        head = self.peek(4)
        if not self.ack_mode and (head[0:1] == b"L" or head[0:2] == b"\x00\x08"):
            if n >= 8:
                length = int.from_bytes(head[2:4], "little") + 8
                if n == length:
                    reply = self.read(n)
                    self.reply.emit(reply)
                elif n > length:
                    packet = self.read(n)
                    self.error.emit(f"overlong packet received: {n=}, {packet=}")

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.read(n)
                self.ack.emit()

        else:
            packet = self.read(n)
            self.error.emit(f"invalid packet received: {n=}, {packet=}")
