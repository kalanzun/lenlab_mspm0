import logging
from typing import Self

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort

from .port_info import PortInfo

logger = logging.getLogger(__name__)


class Terminal(QObject):
    ack = Signal()
    error = Signal(Exception)
    reply = Signal(bytes)
    closed = Signal()

    port: QSerialPort

    def __init__(self):
        super().__init__()

        self.ack_mode = False

    @classmethod
    def from_port_info(cls, port_info: PortInfo) -> Self:
        terminal = cls()
        terminal.port = port_info.create_port()
        return terminal

    @property
    def bytes_available(self) -> int:
        return self.port.bytesAvailable()

    @property
    def port_name(self) -> str:
        return self.port.portName()

    @property
    def is_open(self) -> bool:
        return self.port.isOpen()

    def open(self) -> bool:
        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

        # testing might have put in an open port
        if self.port.isOpen():
            return True

        # port.open emits a NoError on errorOccurred in any case
        # in case of an error, it emits errorOccurred a second time with the error
        # on_error_occurred handles the error case
        logger.debug(f"{self.port_name}: open")
        if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            logger.debug(f"{self.port_name}: open successful")
            self.port.clear()  # windows might have leftovers
            return True

        return False

    def close(self) -> None:
        if self.port.isOpen():
            logger.debug(f"{self.port_name}: close")
            self.port.close()
            self.closed.emit()

    def set_baud_rate(self, baud_rate: int) -> None:
        self.port.setBaudRate(baud_rate)

    def peek(self, n: int) -> bytes:
        return self.port.peek(n).data()

    def read(self, n: int) -> bytes:
        return self.port.read(n).data()

    def write(self, packet: bytes) -> int:
        return self.port.write(packet)

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.DeviceNotFoundError:
            self.error.emit(self.NotFound(self.port_name))
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(self.NoPermission(self.port_name))
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(self.ResourceError(self.port_name))
            self.close()
        else:
            logger.debug(f"{self.port_name}: {self.port.errorString()}")
            self.error.emit(self.OtherError(self.port_name, self.port.errorString()))
            self.close()

    @Slot()
    def on_ready_read(self):
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
                    self.error.emit(self.OverlongPacket(n, packet[:12]))

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.read(n)
                self.ack.emit()

        else:
            packet = self.read(n)
            self.error.emit(self.InvalidPacket(n, packet[:12]))

    class NotFound(Exception):
        pass

    class NoPermission(Exception):
        pass

    class ResourceError(Exception):
        pass

    class OtherError(Exception):
        pass

    class OverlongPacket(Exception):
        pass

    class InvalidPacket(Exception):
        pass
