import logging
from typing import Self

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort

from lenlab.message import Message

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
        terminal.port = QSerialPort(port_info.q_port_info)
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
        logger.debug(f"write {packet}")
        return self.port.write(packet)

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(NoPermission(self.port_name))
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(ResourceError(self.port_name))
        else:
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
                    logger.debug(f"reply {reply[:8]}")
                    self.reply.emit(reply)
                elif n > length:
                    packet = self.read(n)
                    self.error.emit(OverlongPacket(n, packet[:12].hex()))

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.read(n)
                self.ack.emit()

        else:
            packet = self.read(n)
            self.error.emit(InvalidPacket(n, packet[:12].hex()))


class PortError(Message):
    english = """Error on port {0}

    {1}
    """
    german = """Fehler auf Port {0}

    {1}
    """


class NoPermission(PortError):
    english = """Permission denied on port {0}

    Lenlab was not allowed to access the Launchpad port.

    Maybe another instance of Lenlab is running and blocking the port?
    """
    german = """Zugriff verweigert auf Port {0}

    Lenlab erhielt keinen Zugriff auf den Launchpad-Port.

    Vielleicht läuft noch eine andere Instanz von Lenlab und blockiert den Port?
    """


class ResourceError(PortError):
    english = """The Launchpad vanished

    Connect the Launchpad again via USB to your computer.
    """
    german = """
    Das Launchpad ist verschwunden

    Verbinden Sie das Launchpad wieder über USB mit Ihrem Computer.
    """


class TerminalError(Message):
    pass


class OverlongPacket(TerminalError):
    english = """
    Overlong packet received: length = {0}, packet = {1}
    """
    german = """
    Überlanges Paket empfangen: Länge = {0}, Paket = {1}
    """


class InvalidPacket(TerminalError):
    english = """
    Invalid packet received: length = {0}, packet = {1}
    """
    german = """
    Ungültiges Paket empfangen: Länge = {0}, Paket = {1}
    """
