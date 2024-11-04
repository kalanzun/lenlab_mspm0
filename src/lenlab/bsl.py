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
    # Terminal strips the ack
    # ack = int.from_bytes(packet.read(1), byteorder="little")
    # assert ack == 0, "First byte (ack) is not zero"

    header = int.from_bytes(packet.read(1), byteorder="little")
    assert header == 8, "Second byte (head) is not eight"

    length = int.from_bytes(packet.read(2), byteorder="little")
    assert len(packet.getbuffer()) == length + 7, "Invalid reply length"
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

type Callback = Callable[[bytes], None] | None


class BootstrapLoader(QObject):
    finished = Signal(bool)
    message = Signal(Message)

    batch_size = 12 * KB

    connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
    ok_packet = bytes((0x00, 0x08, 0x02, 0x00, 0x3B, 0x06, 0x0D, 0xA7, 0xF7, 0x6B))  # it's actually "invalid command"

    ok = b"\x3b\x00"
    # invalid_command = b"\x3b\x06"

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.ack: Callback = None
        self.reply: Callback = None
        self.device_info: DeviceInfo | None = None
        self.enumerate_batched = None
        self.firmware_size = 0
        self.bsl_reset = True

        self.terminal = terminal
        self.terminal.ack.connect(self.on_ack)
        self.terminal.reply.connect(self.on_reply)

        self.timer = SingleShotTimer(self.on_timeout)

    @Slot(bytes)
    def on_ack(self, packet: bytes):
        # self.message.emit(f"on_ack {packet}")
        try:
            if not self.ack:
                return

            if not self.timer.isActive():
                raise UnexpectedReply(packet)

            self.timer.stop()

            if not packet == b"\x00":
                raise ErrorReply(packet)

            self.ack(packet)

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot(bytes)
    def on_reply(self, packet: bytes):
        # self.message.emit(f"on_reply {packet}")
        try:
            if not self.timer.isActive():
                raise UnexpectedReply(packet)

            self.timer.stop()

            if not self.reply:
                raise UnexpectedReply(packet)

            reply = unpack(BytesIO(packet))
            self.reply(reply)

        except Message as error:
            self.message.emit(error)
            self.finished.emit(False)

    @Slot()
    def on_timeout(self):
        self.message.emit(NoReply())
        self.finished.emit(False)

    def command(self, command: bytearray, ack: Callback | None = None, reply: Callback | None = None, timeout: int = 100):
        self.terminal.write(pack(command))

        self.ack = ack
        self.reply = reply
        self.timer.start(timeout)

    def program(self, firmware: bytes, bsl_reset: bool = True):
        self.enumerate_batched = enumerate(batched(firmware, self.batch_size))
        self.firmware_size = len(firmware)
        self.bsl_reset = bsl_reset

        self.message.emit(Connect())
        self.terminal.port.clear()
        self.terminal.set_baud_rate(9_600)
        self.command(bytearray([0x12]), self.on_connected)

    def on_connected(self, ack: bytes):
        self.message.emit(SetBaudRate())
        self.command(bytearray([0x52, 9]), self.on_baud_rate_changed, timeout=300)

    def on_baud_rate_changed(self, ack: bytes):
        self.terminal.set_baud_rate(3_000_000)

        self.message.emit(GetDeviceInfo())
        self.command(bytearray([0x19]), reply=self.on_device_info)

    def on_device_info(self, reply: bytes):
        self.device_info = DeviceInfo.parse(reply)
        if self.device_info.max_buffer_size < self.batch_size + 8:
            raise BufferTooSmall(self.device_info.max_buffer_size)

        self.message.emit(BufferSize(self.device_info.max_buffer_size / 1000))

        self.message.emit(Unlock())
        self.command(bytearray([0x21] + [0xFF] * 32), reply=self.on_unlocked)

    def on_unlocked(self, reply: bytes):
        if not reply == self.ok:
            raise ErrorReply(reply)

        self.message.emit(Erase())
        self.command(bytearray([0x15]), reply=self.on_erased)

    def on_erased(self, reply: bytes):
        if not reply == self.ok:
            raise ErrorReply(reply)

        self.message.emit(WriteFirmware(self.firmware_size / 1000))
        self.next_batch()

    def next_batch(self):
        i, batch = next(self.enumerate_batched)
        payload = bytearray([0x24])
        payload.extend((i * self.batch_size).to_bytes(4, byteorder="little"))
        payload.extend(batch)

        self.command(payload, self.on_programmed, timeout=300)

    def on_programmed(self, ack: bytes):
        try:
            self.next_batch()
        except StopIteration:
            if self.bsl_reset:
                self.message.emit(Restart())
                self.command(bytearray([0x40]), self.on_reset)
            else:
                self.finished.emit(True)

    def on_reset(self, ack: bytes):
        self.finished.emit(True)


class UnexpectedReply(Message):
    english = "Unexpected reply received: {0}"
    german = "Unerwartete Antwort erhalten: {0}"


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
