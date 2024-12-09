import logging

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort

from ..message import Message

logger = logging.getLogger(__name__)


class Terminal(QObject):
    ack = Signal()
    error = Signal(Message)
    reply = Signal(bytes)
    closed = Signal()

    def __init__(self, port: QSerialPort | None = None):
        super().__init__()
        self.port = port

        self.ack_mode = False

    @property
    def port_name(self) -> str:
        return self.port.portName()

    @property
    def bytes_available(self) -> int:
        return self.port.bytesAvailable()

    @property
    def is_open(self):
        return self.port.isOpen()

    def set_baud_rate(self, baud_rate: int):
        logger.debug(f"{self.port_name}: set_baud_rate:  {baud_rate}")
        self.port.setBaudRate(baud_rate)

    def open(self) -> bool:
        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

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
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(TerminalPermissionError())
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(TerminalResourceError())
        else:
            logger.debug(f"{self.port_name}: {self.port.errorString()}")
            self.error.emit(TerminalError(self.port_name, self.port.errorString()))

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
                    self.error.emit(OverlongPacket(n, packet[:12]))

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.read(n)
                self.ack.emit()

        else:
            packet = self.read(n)
            self.error.emit(InvalidPacket(n, packet[:12]))


class TerminalError(Message):
    english = "Error on {0}: {1}"
    german = "Fehler auf {0}: {1}"


class TerminalPermissionError(Message):
    english = """### Permission error

    Lenlab requires unique access to the serial communication with the Launchpad.
    Maybe another instance of Lenlab is running and blocks the access?"""

    german = """### Keine Zugriffsberechtigung

    Lenlab braucht alleinigen Zugriff auf die serielle Kommunikation mit dem Launchpad.
    Vielleicht läuft noch eine andere Instanz von Lenlab und blockiert den Zugriff?"""


class TerminalResourceError(Message):
    english = """### Connection lost

    The Launchpad vanished. Please reconnect it to the computer."""

    german = """### Verbindung verloren

    Das Launchpad ist verschwunden. Bitte wieder mit dem Computer verbinden."""


class OverlongPacket(Message):
    english = "Overlong packet received: length = {0}, packet = {1}"
    german = "Überlanges Paket empfangen: Länge = {0}, Paket = {1}"


class InvalidPacket(Message):
    english = "Invalid packet received: length = {0}, packet = {1}"
    german = "Ungültiges Paket empfangen: Länge = {0}, Paket = {1}"
