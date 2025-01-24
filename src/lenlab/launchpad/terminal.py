import logging
from typing import Self

from attrs import frozen
from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort

from ..message import Message
from .port_info import PortInfo

logger = logging.getLogger(__name__)


class Terminal(QObject):
    ack = Signal()
    error = Signal(Message)
    reply = Signal(bytes)

    port: QSerialPort

    def __init__(self, port_name: str = ""):
        super().__init__()

        self.ack_mode = False
        self.port_name = port_name

    @classmethod
    def from_port_info(cls, port_info: PortInfo) -> Self:
        terminal = cls(port_info.name)
        terminal.port = port_info.create_port()
        return terminal

    @property
    def bytes_available(self) -> int:
        return self.port.bytesAvailable()

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
        logger.debug(f"open {self.port_name}")
        if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            self.port.clear()  # windows might have leftovers
            return True

        return False

    def close(self) -> None:
        if self.port.isOpen():
            logger.debug(f"close {self.port_name}")
            self.port.close()

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
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(NoPermission(self.port_name))
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.close()
            self.error.emit(ResourceError())
        else:
            self.close()
            logger.debug(f"{self.port_name}: {self.port.errorString()}")
            self.error.emit(PortError(self.port_name, self.port.errorString()))

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
                    logger.error(f"Overlong packet received: length = {n}, packet = {packet[:12]}")

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.read(n)
                self.ack.emit()

        else:
            packet = self.read(n)
            logger.error(f"Invalid packet received: length = {n}, packet = {packet[:12]}")


@frozen
class LaunchpadError(Message):
    pass


@frozen
class NoPermission(LaunchpadError):
    port_name: str
    english = """Permission denied on the Launchpad port {port_name}

    Lenlab was not allowed to access the Launchpad port.
    
    Maybe another instance of Lenlab is running and blocking the port?
    """
    german = """Zugriff verweigert auf den Launchpad-Port {port_name}
    
    Lenlab wurde der Zugriff auf den Launchpad-Port nicht erlaubt.
    
    Vielleicht läuft noch eine andere Instanz von Lenlab und blockiert den Port?
    """


@frozen
class ResourceError(LaunchpadError):
    english = """The Launchpad vanished
    
    Connect the Launchpad via USB to your computer again.
    """
    german = """
    Das Launchpad ist verschwunden.
    
    Verbinden Sie das Launchpad wieder über USB mit Ihrem Computer.
    """


@frozen
class PortError(LaunchpadError):
    port_name: str
    text: str
    english = """Other error on port {port_name}
    
    {text}
    """
    german = """Anderer Fehler auf Port {port_name}
    
    {text}
    """
