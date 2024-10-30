from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort


class Terminal(QObject):
    ack = Signal(bytes)
    error = Signal(str)
    reply = Signal(bytes)

    def __init__(self, port: QSerialPort):
        super().__init__()
        self.port = port

        self.firmware = False
        self.bsl = False

        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

    @property
    def port_name(self) -> str:
        return self.port.portName()

    def set_baud_rate(self, baud_rate: int):
        self.port.setBaudRate(baud_rate)

    def open(self) -> bool:
        # port.open emits a NoError on errorOccurred in any case
        # in case of an error, it emits errorOccurred a second time with the error
        # on_error_occurred handles the error case
        return self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

    def close(self) -> None:
        if self.port.isOpen():
            self.port.close()

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
        n = self.port.bytesAvailable()
        if n == 1:
            # If the OS delivered the single ack byte of a BSL core response alone
            # and if this handler read it, the core response would become invalid
            ack = self.port.peek(1).data()
            if ack in b"\x00QRSTUV":  # 0x51 - 0x56
                self.ack.emit(ack)  # note, it did not remove the ack from the buffer

        if n >= 8:
            head = self.port.peek(4).data()
            if head[0:1] == b"L" or head[0:2] == b"\x00\x08":
                length = int.from_bytes(head[2:4], "little") + 8
                if n == length:
                    reply = self.read(n)
                    self.reply.emit(reply)
                elif n > length:
                    self.read(n)
                    self.error.emit(f"overlong packet received: {n=}, {head=}")

            else:
                self.read(n)
                self.error.emit(f"invalid packet received: {head=}")
