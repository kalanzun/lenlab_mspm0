from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort


class Terminal(QObject):
    ack = Signal(bytes)  # bsl only
    error = Signal(str)
    reply = Signal(bytes)  # replies loose the prefix 'L'

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

    def set_baud_rate(self, baud_rate: int) -> None:
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
        while self.port.bytesAvailable() and self.port.peek(1).data() in b"L\x00QRSTUV":  # 0x51 - 0x56
            ack = self.read(1)
            if ack == b"\x00":
                self.ack.emit(ack)
            elif ack != b"L":
                self.error.emit(f"error byte received: {ack}")

        n = self.port.bytesAvailable()
        if n >= 7:
            head = self.port.peek(3).data()
            if head[0] == ord("l") or head[0] == 8:
                length = int.from_bytes(head[1:3], "little") + 7
                if n >= length:
                    reply = self.read(n)
                    self.reply.emit(reply)
                    if n > length:
                        self.on_ready_read()
            else:
                data = self.read(n)
                self.error.emit(f"invalid data received: {n=}, {data=}")
