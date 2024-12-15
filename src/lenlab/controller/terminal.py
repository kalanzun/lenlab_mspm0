from typing import Self

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort

from ..message import Message
from ..model.port_info import PortInfo


class Terminal(QObject):
    ack = Signal()
    error = Signal(Message)
    reply = Signal(bytes)

    port: QSerialPort

    def __init__(self):
        super().__init__()
        self.ack_mode = False

    @classmethod
    def from_port_info(cls, port_info: PortInfo) -> Self:
        terminal = cls()
        terminal.port = QSerialPort(port_info.q_port_info)
        return terminal

    def open(self) -> bool:
        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

        # port.open emits a NoError on errorOccurred in any case
        # in case of an error, it emits errorOccurred a second time with the error
        # on_error_occurred ignores NoError or handles the error case
        if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            self.port.clear()  # windows might have leftovers
            return True

        return False

    def close(self) -> None:
        self.port.close()

    @property
    def port_name(self) -> str:
        return self.port.portName()

    def set_baud_rate(self, baud_rate: int) -> None:
        self.port.setBaudRate(baud_rate)

    def peek(self, n: int) -> bytes:
        return self.port.peek(n).data()

    def read(self, n: int) -> bytes:
        return self.port.read(n).data()

    def write(self, packet: bytes) -> int:
        return self.port.write(packet)

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error: QSerialPort.SerialPortError):
        if error is QSerialPort.SerialPortError.NoError:
            return

        self.error.emit(PortError(error, self.port.errorString()))

    @Slot()
    def on_ready_read(self, n: int) -> None:
        head = self.peek(4)
        if not self.ack_mode and (head[0:1] == b"L" or head[0:2] == b"\x00\x08"):
            if n >= 8:
                length = int.from_bytes(head[2:4], "little") + 8
                if n == length:
                    reply = self.read(n)
                    self.reply.emit(reply)
                elif n > length:
                    packet = self.read(n)
                    self.error.emit(OverlongPacket(n, packet[:12]))

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.read(n)
                self.ack.emit()

        else:
            packet = self.read(n)
            self.error.emit(InvalidPacket(n, packet[:12]))


class PortError(Message):
    english = "{1}"
    german = "{1}"


class OverlongPacket(Message):
    english = "Overlong packet received: length = {0}, packet = {1}"
    german = "Überlanges Paket empfangen: Länge = {0}, Paket = {1}"


class InvalidPacket(Message):
    english = "Invalid packet received: length = {0}, packet = {1}"
    german = "Ungültiges Paket empfangen: Länge = {0}, Paket = {1}"
