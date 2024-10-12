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


@dataclass(frozen=True)
class BSLInteger:
    """Encode and decode Bootstrap Loader integers in binary little endian format."""

    n_bytes: int

    def pack(self, value: int) -> bytearray:
        return bytearray((value >> (8 * i)) & 0xFF for i in range(self.n_bytes))

    def unpack(self, packet: BytesIO) -> int:
        message = packet.read(self.n_bytes)
        assert len(message) == self.n_bytes, "Message too short"
        return sum(message[i] << (8 * i) for i in range(self.n_bytes))


uint8 = BSLInteger(1)
uint16 = BSLInteger(2)
uint32 = BSLInteger(4)


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


def pack(payload: bytes) -> bytearray:
    """Pack a packet for the Bootstrap Loader."""
    return bytearray().join(
        [
            uint8.pack(0x80),
            uint16.pack(len(payload)),
            payload,
            uint32.pack(checksum(payload)),
        ]
    )


def unpack(packet: BytesIO) -> bytes:
    """Unpack a packet from the Bootstrap Loader and verify the checksum."""
    ack = uint8.unpack(packet)
    assert ack == 0, "First byte (ack) is not zero"

    header = uint8.unpack(packet)
    assert header == 8, "Second byte (header) is not eight"

    length = uint16.unpack(packet)
    assert len(packet.getbuffer()) == length + 8, "Invalid reply length"
    payload = packet.read(length)

    crc = uint32.unpack(packet)
    if not checksum(payload) == crc:
        raise ChecksumError()

    return payload


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
        return cls(*(field.type.unpack(packet) for field in fields(cls)))


KB = 1024


class BootstrapLoader(QObject):
    finished = Signal(bool)
    message = Signal(Message)

    batch_size = 12 * KB

    ACK = b"\x00"
    OK = b"\x3b\x00"

    def __init__(self, launchpad: Launchpad):
        super().__init__()

        self.callback: Callable[[bytes], None] | None = None
        self.device_info: DeviceInfo | None = None
        self.enumerate_batched = None
        self.firmware_size = 0

        self.launchpad = launchpad
        self.launchpad.bsl_reply.connect(self.on_bsl_reply)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)

    @Slot(bytes)
    def on_bsl_reply(self, packet: bytes) -> None:
        try:
            if not self.timer.isActive():
                raise UnexpectedReply()

            self.timer.stop()

            reply = packet if len(packet) == 1 else unpack(BytesIO(packet))
            self.callback(reply)

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot()
    def on_timeout(self):
        self.message.emit(NoReply())
        self.finished.emit(False)

    def program(self, firmware: bytes):
        self.enumerate_batched = enumerate(batched(firmware, self.batch_size))
        self.firmware_size = len(firmware)

        self.message.emit(Connect())
        self.launchpad.port.setBaudRate(9600)
        self.command(bytearray([0x12]), self.on_connected)

    def command(self, command, callback, timeout=100):
        self.launchpad.port.write(pack(command))
        self.callback = callback
        self.timer.start(timeout)

    def on_connected(self, reply):
        if not (reply == self.ACK or reply == self.OK):
            raise ErrorReply(reply)

        self.message.emit(SetBaudRate())
        self.command(bytearray([0x52, 9]), self.on_baud_rate_changed)

    def on_baud_rate_changed(self, reply):
        if not reply == self.ACK:
            raise ErrorReply(reply)

        self.launchpad.port.setBaudRate(3_000_000)

        self.message.emit(GetDeviceInfo())
        self.command(bytearray([0x19]), self.on_device_info)

    def on_device_info(self, reply):
        self.device_info = DeviceInfo.parse(reply)
        if self.device_info.max_buffer_size < self.batch_size + 8:
            raise BufferTooSmall(self.device_info.max_buffer_size)

        self.message.emit(BufferSize(self.device_info.max_buffer_size / 1000))

        self.message.emit(Unlock())
        self.command(bytearray([0x21] + [0xFF] * 32), self.on_unlocked)

    def on_unlocked(self, reply):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(Erase())
        self.command(bytearray([0x15]), self.on_erased)

    def on_erased(self, reply):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(WriteFirmware(self.firmware_size / 1000))
        self.next_batch()

    def next_batch(self):
        i, batch = next(self.enumerate_batched)
        payload = bytearray([0x24])
        payload.extend(uint32.pack(i * self.batch_size))
        payload.extend(batch)

        self.command(payload, self.on_programmed, timeout=300)

    def on_programmed(self, reply):
        if not reply == self.ACK:
            raise ErrorReply(reply)

        try:
            self.next_batch()
        except StopIteration:
            self.message.emit(Restart())
            self.command(bytearray([0x40]), self.on_reset)

    def on_reset(self, reply):
        if not reply == self.ACK:
            raise ErrorReply(reply)

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
