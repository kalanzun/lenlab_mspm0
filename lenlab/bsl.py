"""MSPM0 Bootstrap Loader (BSL)

The MSPM0 Bootstrap Loader (BSL) provides a method to program and verify the device memory
(Flash and RAM) through a standard serial interface (UART or I2C).

User's Guide https://www.ti.com/lit/ug/slau887/slau887.pdf
"""

from dataclasses import dataclass, fields
from io import BytesIO
from itertools import batched
from typing import Callable, Self

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from .launchpad import Launchpad
from .message import Message


crc_polynom = 0xEDB88320


def checksum(payload: bytes) -> int:
    """Calculate the Bootstrap Loader checksum."""
    crc = 0xFFFFFFFF
    for byte in payload:
        crc = crc ^ byte
        for _ in range(8):
            mask = -(crc & 1)
            crc = (crc >> 1) ^ (crc_polynom & mask)
    return crc


def pack(payload: bytes) -> bytes:
    """Pack a packet for the Bootstrap Loader."""
    packet = BytesIO()
    packet.write((0x80).to_bytes(1, byteorder="little"))
    packet.write(len(payload).to_bytes(2, byteorder="little"))
    packet.write(payload)
    packet.write(checksum(payload).to_bytes(4, byteorder="little"))
    return packet.getvalue()


def unpack(packet: BytesIO) -> bytes:
    """Unpack a packet from the Bootstrap Loader and verify the checksum."""
    header = int.from_bytes(packet.read(1), byteorder="little")
    assert header == 8, "First byte (header) is not eight"

    length = int.from_bytes(packet.read(2), byteorder="little")
    assert len(packet.getbuffer()) == length + 7, "Invalid reply length"
    payload = packet.read(length)

    crc = int.from_bytes(packet.read(4), byteorder="little")
    if not checksum(payload) == crc:
        raise ChecksumError()

    return payload


class uint8(int):
    n_bytes = 1


class uint16(int):
    n_bytes = 2


class uint32(int):
    n_bytes = 4


@dataclass(frozen=True)
class DeviceInfo:
    response: uint8
    command_interpreter_version: uint16
    build_id: uint16
    application_version: uint32
    interface_version: uint16
    max_buffer_size: uint16
    buffer_start_address: uint32
    bcr_configuration_id: uint32
    bsl_configuration_id: uint32

    @classmethod
    def parse(cls, reply: bytes) -> Self:
        packet = BytesIO(reply)
        return cls(*(field.type.from_bytes(packet.read(field.type.n_bytes), byteorder="little") for field in fields(cls)))


KB = 1024

Callback = Callable[[bytes], None] | None


class BootstrapLoader(QObject):
    finished = Signal(bool)
    message = Signal(Message)

    batch_size = 12 * KB

    OK = b"\x3b\x00"

    def __init__(self, launchpad: Launchpad):
        super().__init__()

        self.ack_callback: Callback = None
        self.reply_callback: Callback = None
        self.device_info: DeviceInfo | None = None
        self.enumerate_batched = None
        self.firmware_size = 0

        self.launchpad = launchpad
        self.launchpad.bsl_ack.connect(self.on_bsl_ack)
        self.launchpad.bsl_reply.connect(self.on_bsl_reply)

        self.ack_timer = QTimer()
        self.ack_timer.setSingleShot(True)
        self.ack_timer.timeout.connect(self.on_timeout)

        self.reply_timer = QTimer()
        self.reply_timer.setSingleShot(True)
        self.reply_timer.timeout.connect(self.on_timeout)

    @Slot(bytes)
    def on_bsl_ack(self, packet: bytes) -> None:
        try:
            if not self.ack_timer.isActive():
                raise UnexpectedReply()

            self.ack_timer.stop()

            if not packet == b"\x00":
                raise ErrorReply(packet)

            if self.ack_callback is not None:
                self.ack_callback(packet)

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot(bytes)
    def on_bsl_reply(self, packet: bytes) -> None:
        try:
            if not self.reply_timer.isActive():
                raise UnexpectedReply()

            self.reply_timer.stop()

            reply = unpack(BytesIO(packet))
            self.reply_callback(reply)

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot()
    def on_timeout(self):
        self.message.emit(NoReply())
        self.finished.emit(False)

    def command(self, command: bytearray, ack_callback: Callback = None, reply_callback: Callback = None, timeout: int = 100):
        self.launchpad.port.write(pack(command))

        self.ack_callback = ack_callback
        self.ack_timer.start(timeout)

        self.reply_callback = reply_callback
        if reply_callback is not None:
            self.reply_timer.start(timeout)

    def program(self, firmware: bytes):
        self.enumerate_batched = enumerate(batched(firmware, self.batch_size))
        self.firmware_size = len(firmware)

        self.message.emit(Connect())
        self.launchpad.port.setBaudRate(9600)
        self.command(bytearray([0x12]), self.on_connected)

    def on_connected(self, reply):
        self.message.emit(SetBaudRate())
        self.command(bytearray([0x52, 9]), self.on_baud_rate_changed)

    def on_baud_rate_changed(self, reply):
        self.launchpad.port.setBaudRate(3_000_000)

        self.message.emit(GetDeviceInfo())
        self.command(bytearray([0x19]), reply_callback=self.on_device_info)

    def on_device_info(self, reply):
        self.device_info = DeviceInfo.parse(reply)
        if self.device_info.max_buffer_size < self.batch_size + 8:
            raise BufferTooSmall(self.device_info.max_buffer_size)

        self.message.emit(BufferSize(self.device_info.max_buffer_size / 1000))

        self.message.emit(Unlock())
        self.command(bytearray([0x21] + [0xFF] * 32), reply_callback=self.on_unlocked)

    def on_unlocked(self, reply):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(Erase())
        self.command(bytearray([0x15]), reply_callback=self.on_erased)

    def on_erased(self, reply):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(WriteFirmware(self.firmware_size / 1000))
        self.next_batch()

    def next_batch(self):
        i, batch = next(self.enumerate_batched)
        payload = bytearray([0x24])
        payload.extend((i * self.batch_size).to_bytes(4, byteorder="little"))
        payload.extend(batch)

        self.command(payload, self.on_programmed, timeout=300)

    def on_programmed(self, reply):
        try:
            self.next_batch()
        except StopIteration:
            self.message.emit(Restart())
            self.command(bytearray([0x40]), self.on_reset)

    def on_reset(self, reply):
        self.finished.emit(True)
        self.launchpad.ready.emit()


class UnexpectedReply(Message):
    english = "Unexpected reply received"
    german = "Unerwartete Antwort erhalten"


class ChecksumError(Message):
    english = "Checksum verification failed"
    german = "Fehlerhafte Prüfsumme"


class ErrorReply(Message):
    english = "Error message received: {0}"
    german = "Fehlermeldung erhalten: {0}"


class NoReply(Message):
    english = "No reply received"
    german = "Keine Antwort erhalten"


class Connect(Message):
    english = "Establish connection"
    german = "Verbindung aufbauen"


class SetBaudRate(Message):
    english = "Set baudrate"
    german = "Baudrate einstellen"


class GetDeviceInfo(Message):
    english = "Get device info"
    german = "Controller-Eigenschaften abrufen"


class BufferTooSmall(Message):
    english = "Buffer too small"
    german = "Die Puffergröße im Controller ist zu klein"


class BufferSize(Message):
    english = "Max. buffer size: {0:.1f} KiB"
    german = "Max. Puffergröße: {0:.1f} KiB"


class Unlock(Message):
    english = "Unlock Bootstrap Loader"
    german = "Bootstrap Loader entsperren"


class Erase(Message):
    english = "Erase memory"
    german = "Speicher löschen"


class WriteFirmware(Message):
    english = "Write firmware ({0:.1f} KiB)"
    german = "Firmware schreiben ({0:.1f} KiB)"


class Restart(Message):
    english = "Restart"
    german = "Neustarten"
