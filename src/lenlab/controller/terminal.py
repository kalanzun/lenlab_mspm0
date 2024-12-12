from PySide6.QtCore import QObject, Signal, Slot

from ..model.message import Message
from ..model.port import Port


class Terminal(QObject):
    ack = Signal()
    error = Signal(Message)
    reply = Signal(bytes)
    closed = Signal()

    def __init__(self, port: Port):
        super().__init__()
        self.port = port

        self.ack_mode = False

    def open(self) -> bool:
        self.port.error.connect(self.on_port_error)
        self.port.ready_read.connect(self.on_ready_read)

        # port.open emits a NoError on errorOccurred in any case
        # in case of an error, it emits errorOccurred a second time with the error
        # on_error_occurred handles the error case
        if self.port.open():
            self.port.clear()  # windows might have leftovers
            return True

        return False

    def close(self) -> None:
        if self.port.is_open:
            self.port.close()
            self.closed.emit()

    def set_baud_rate(self, baud_rate: int) -> None:
        self.port.set_baud_rate(baud_rate)

    def write(self, packet: bytes) -> None:
        self.port.write(packet)

    @Slot(Message)
    def on_port_error(self, error: Message) -> None:
        self.error.emit(error)

    @Slot()
    def on_ready_read(self, n: int) -> None:
        head = self.port.peek(4)
        if not self.ack_mode and (head[0:1] == b"L" or head[0:2] == b"\x00\x08"):
            if n >= 8:
                length = int.from_bytes(head[2:4], "little") + 8
                if n == length:
                    reply = self.port.read(n)
                    self.reply.emit(reply)
                elif n > length:
                    packet = self.port.read(n)
                    self.error.emit(OverlongPacket(n, packet[:12]))

        # a single zero is valid in both modes
        elif n == 1 and head[0:1] == b"\x00":
            if self.ack_mode:
                self.port.read(n)
                self.ack.emit()

        else:
            packet = self.port.read(n)
            self.error.emit(InvalidPacket(n, packet[:12]))


class OverlongPacket(Message):
    english = "Overlong packet received: length = {0}, packet = {1}"
    german = "Überlanges Paket empfangen: Länge = {0}, Paket = {1}"


class InvalidPacket(Message):
    english = "Invalid packet received: length = {0}, packet = {1}"
    german = "Ungültiges Paket empfangen: Länge = {0}, Paket = {1}"
