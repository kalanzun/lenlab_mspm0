from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort

from lenlab.model.message import Message
from lenlab.model.port_info import PortInfo


class Port(QObject):
    error = Signal(Message)
    ready_read = Signal(int)

    def __init__(self, port: QSerialPort):
        super().__init__()

        self.port = port

    @classmethod
    def from_port_info(cls, port_info: PortInfo):
        return cls(QSerialPort(port_info.q_port_info))

    @property
    def is_open(self) -> bool:
        return self.port.isOpen()

    @property
    def port_name(self) -> str:
        return self.port.portName()

    def set_baud_rate(self, baud_rate: int) -> None:
        self.port.setBaudRate(baud_rate)

    def open(self) -> bool:
        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

        # port.open emits a NoError on errorOccurred in any case
        # in case of an error, it emits errorOccurred a second time with the error
        # on_error_occurred ignores NoError and handles the error case
        return self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

    def close(self) -> None:
        self.port.close()

    def peek(self, n: int) -> bytes:
        return self.port.peek(n).data()

    def read(self, n: int) -> bytes:
        return self.port.read(n).data()

    def write(self, packet: bytes) -> int:
        return self.port.write(packet)

    def clear(self) -> None:
        self.port.clear()

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error: QSerialPort.SerialPortError):
        if error is QSerialPort.SerialPortError.NoError:
            return

        self.error.emit(PortError(error, self.port.errorString()))

    @Slot()
    def on_ready_read(self):
        self.ready_read.emit(self.port.bytesAvailable())


class PortError(Message):
    english = "Serial port error: {1}"
    german = "Fehler im seriellen Port: {1}"
