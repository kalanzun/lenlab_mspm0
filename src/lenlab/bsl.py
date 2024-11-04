"""MSPM0 Bootstrap Loader (BSL)

The MSPM0 Bootstrap Loader (BSL) provides a method to program and verify the device memory
(Flash and RAM) through a standard serial interface (UART or I2C).

User's Guide https://www.ti.com/lit/ug/slau887/slau887.pdf
"""

import struct
from collections.abc import Callable
from dataclasses import dataclass, fields
from io import BytesIO
from itertools import batched
from typing import Self

from PySide6.QtCore import QObject, Signal, Slot

from lenlab.launchpad import crc, last
from lenlab.singleshot import SingleShotTimer
from lenlab.terminal import Terminal

from .message import Message


def pack(payload: bytes) -> bytes:
    """Pack a packet for the Bootstrap Loader."""
    return b"".join(
        [
            (0x80).to_bytes(1, byteorder="little"),
            len(payload).to_bytes(2, byteorder="little"),
            payload,
            last(crc(payload)).to_bytes(4, byteorder="little"),
        ]
    )


def unpack(packet: BytesIO) -> bytes:
    """Unpack a packet from the Bootstrap Loader and verify the checksum."""
    ack = int.from_bytes(packet.read(1), byteorder="little")
    assert ack == 0, "First byte (ack) is not zero"

    header = int.from_bytes(packet.read(1), byteorder="little")
    assert header == 8, "Second byte (header) is not eight"

    length = int.from_bytes(packet.read(2), byteorder="little")
    assert len(packet.getbuffer()) == length + 8, "Invalid reply length"
    payload = packet.read(length)

    checksum = int.from_bytes(packet.read(4), byteorder="little")
    if not last(crc(payload)) == checksum:
        raise ChecksumError()

    return payload


type Byte = int  # uint8
type Half = int  # uint16
type Long = int  # uint32


@dataclass(slots=True, frozen=True)
class DeviceInfo:
    response: Byte
    command_interpreter_version: Half
    build_id: Half
    application_version: Long
    interface_version: Half
    max_buffer_size: Half
    buffer_start_address: Long
    bcr_configuration_id: Long
    bsl_configuration_id: Long

    @classmethod
    def parse(cls, reply: bytes) -> Self:
        fmt = "<" + "".join(str(field.type)[0] for field in fields(cls))
        return cls(*struct.unpack(fmt, reply))


KB = 1024


class BootstrapLoader(QObject):
    finished = Signal(bool)
    message = Signal(Message)

    batch_size = 12 * KB

    connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))

    OK = b"\x3b\x00"

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.callback: Callable[..., None] | None = None
        self.device_info: DeviceInfo | None = None
        self.enumerate_batched = None
        self.firmware_size = 0

        self.terminal = terminal
        self.terminal.ack.connect(self.on_ack)
        self.terminal.reply.connect(self.on_reply)

        self.timer = SingleShotTimer(self.on_timeout)

    @Slot()
    def on_ack(self):
        try:
            if not self.timer.isActive():
                raise UnexpectedReply()

            self.timer.stop()
            self.callback()

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot(bytes)
    def on_reply(self, packet: bytes):
        try:
            if not self.timer.isActive():
                raise UnexpectedReply()

            self.timer.stop()
            reply = unpack(BytesIO(packet))
            self.callback(reply)

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot()
    def on_timeout(self):
        self.message.emit(NoReply())
        self.finished.emit(False)

    def command(self, command: bytearray, callback: Callable[..., None], ack_mode: bool = False, timeout: int = 100):
        self.terminal.ack_mode = ack_mode
        self.terminal.write(pack(command))

        self.callback = callback
        self.timer.start(timeout)

    def program(self, firmware: bytes):
        self.enumerate_batched = enumerate(batched(firmware, self.batch_size))
        self.firmware_size = len(firmware)

        self.message.emit(Connect())
        self.terminal.port.clear()
        self.terminal.set_baud_rate(9_600)
        self.command(bytearray([0x12]), self.on_connected, ack_mode=True)

    def on_connected(self):
        self.message.emit(SetBaudRate())
        self.command(bytearray([0x52, 9]), self.on_baud_rate_changed, ack_mode=True)

    def on_baud_rate_changed(self):
        self.terminal.set_baud_rate(3_000_000)

        self.message.emit(GetDeviceInfo())
        self.command(bytearray([0x19]), self.on_device_info)

    def on_device_info(self, reply: bytes):
        self.device_info = DeviceInfo.parse(reply)
        if self.device_info.max_buffer_size < self.batch_size + 8:
            raise BufferTooSmall(self.device_info.max_buffer_size)

        self.message.emit(BufferSize(self.device_info.max_buffer_size / 1000))

        self.message.emit(Unlock())
        self.command(bytearray([0x21] + [0xFF] * 32), self.on_unlocked)

    def on_unlocked(self, reply: bytes):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(Erase())
        self.command(bytearray([0x15]), self.on_erased)

    def on_erased(self, reply: bytes):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(WriteFirmware(self.firmware_size / 1000))
        self.next_batch()

    def next_batch(self):
        i, batch = next(self.enumerate_batched)
        payload = bytearray([0x24])
        payload.extend((i * self.batch_size).to_bytes(4, byteorder="little"))
        payload.extend(batch)

        self.command(payload, self.on_programmed, ack_mode=True, timeout=300)

    def on_programmed(self):
        try:
            self.next_batch()
        except StopIteration:
            self.message.emit(Restart())
            self.command(bytearray([0x40]), self.on_reset, ack_mode=True)

    def on_reset(self):
        self.finished.emit(True)


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
