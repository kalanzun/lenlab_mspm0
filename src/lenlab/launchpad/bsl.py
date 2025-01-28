"""MSPM0 Bootstrap Loader (BSL)

The MSPM0 Bootstrap Loader (BSL) provides a method to program and verify the device memory
(Flash and RAM) through a standard serial interface (UART or I2C).

User's Guide https://www.ti.com/lit/ug/slau887/slau887.pdf
"""

import logging
import struct
from collections.abc import Callable
from io import BytesIO
from itertools import batched
from typing import Self

from attrs import fields, frozen
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from ..message import Message
from .launchpad import KB, crc, last
from .terminal import Terminal

logger = logging.getLogger(__name__)


def pack(payload: bytes) -> bytes:
    """Pack a packet for the Bootstrap Loader."""
    return b"".join(
        [
            b"\x80",
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


@frozen
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
        # the first letter of the type happens to be the format code for struct.unpack
        fmt = "<" + "".join(str(field.type)[0] for field in fields(cls))
        return cls(*struct.unpack(fmt, reply))


class BootstrapLoader(QObject):
    message = Signal(Message)
    success = Signal(Terminal)
    error = Signal(Message)

    batch_size = 12 * KB
    interval = 600

    # connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
    CONNECT = b"\x12"
    OK = b"\x3b\x00"

    terminal: Terminal
    callback: Callable[..., None]
    device_info: DeviceInfo
    enumerate_batched: enumerate
    firmware_size: int

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal
        self.unsuccessful = False

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.on_timeout)

    def start(self, firmware: bytes):
        self.enumerate_batched = enumerate(batched(firmware, self.batch_size))
        self.firmware_size = len(firmware)

        self.terminal.ack.connect(self.on_ack)
        self.terminal.reply.connect(self.on_reply)
        self.terminal.error.connect(self.on_error)

        self.terminal.set_baud_rate(9_600)
        self.command(self.CONNECT, self.on_connected, ack_mode=True)

    def command(
        self,
        command: bytes,
        callback: Callable[..., None],
        ack_mode: bool = False,
    ):
        self.terminal.ack_mode = ack_mode
        self.terminal.write(pack(command))

        self.callback = callback
        self.timer.start()

    @Slot()
    def on_ack(self):
        try:
            if not self.timer.isActive():
                raise UnexpectedReply()

            self.timer.stop()
            self.callback()

        except Message as error:
            self.unsuccessful = True
            self.error.emit(error)

    @Slot(bytes)
    def on_reply(self, packet: bytes):
        try:
            if not self.timer.isActive():
                raise UnexpectedReply()

            self.timer.stop()
            reply = unpack(BytesIO(packet))
            self.callback(reply)

        except Message as error:
            self.unsuccessful = True
            self.error.emit(error)

    @Slot(Message)
    def on_error(self, error: Message):
        self.timer.stop()
        self.unsuccessful = True
        self.error.emit(error)

    @Slot()
    def on_timeout(self):
        self.unsuccessful = True
        self.error.emit(NoReply(self.terminal.port_name))

    def on_connected(self):
        self.message.emit(Connected(self.terminal.port_name))
        self.message.emit(SetBaudRate("1 MBaud"))
        # 7: 1 MBaud
        self.command(bytes([0x52, 7]), self.on_baud_rate_changed, ack_mode=True)

    def on_baud_rate_changed(self):
        self.terminal.set_baud_rate(1_000_000)

        self.message.emit(GetDeviceInfo())
        self.command(bytes([0x19]), self.on_device_info)

    def on_device_info(self, reply: bytes):
        self.device_info = DeviceInfo.parse(reply)
        if self.device_info.max_buffer_size < self.batch_size + 8:
            raise BufferTooSmall(self.device_info.max_buffer_size)

        self.message.emit(BufferSize(self.device_info.max_buffer_size / 1000))

        self.message.emit(Unlock())
        self.command(bytes([0x21] + [0xFF] * 32), self.on_unlocked)

    def on_unlocked(self, reply: bytes):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(Erase())
        self.command(bytes([0x15]), self.on_erased)

    def on_erased(self, reply: bytes):
        if not reply == self.OK:
            raise ErrorReply(reply)

        self.message.emit(WriteFirmware(self.firmware_size / 1000))
        self.next_batch()

    def next_batch(self):
        # batch is a tuple of ints (single bytes)
        i, batch = next(self.enumerate_batched)
        payload = b"".join(
            [
                b"\x24",
                (i * self.batch_size).to_bytes(4, byteorder="little"),
                bytes(batch),
            ]
        )
        self.command(payload, self.on_programmed, ack_mode=True)

    def on_programmed(self):
        try:
            self.next_batch()
        except StopIteration:
            self.message.emit(Restart())
            self.command(bytes([0x40]), self.on_restart, ack_mode=True)

    def on_restart(self):
        self.success.emit(self.terminal)


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
    english = "No reply received on {0}"
    german = "Keine Antwort erhalten auf {0}"


class Cancelled(Message):
    english = "Cancelled on {0}"
    german = "Abgebrochen auf {0}"


class Connect(Message):
    english = "Establish connection on {0}"
    german = "Verbindung aufbauen auf {0}"


class Connected(Message):
    english = "Connected on {0}"
    german = "Verbunden auf {0}"
    progress = 1


class SetBaudRate(Message):
    english = "Set baudrate: {0}"
    german = "Baudrate einstellen: {0}"
    progress = 1


class GetDeviceInfo(Message):
    english = "Get device info"
    german = "Controller-Eigenschaften abrufen"
    progress = 1


class BufferTooSmall(Message):
    english = "Buffer too small: {0:.1f} KiB"
    german = "Die Puffergröße ist zu klein: {0:.1f} KiB"


class BufferSize(Message):
    english = "Max. buffer size: {0:.1f} KiB"
    german = "Max. Puffergröße: {0:.1f} KiB"
    progress = 1


class Unlock(Message):
    english = "Unlock Bootstrap Loader"
    german = "Bootstrap Loader entsperren"
    progress = 1


class Erase(Message):
    english = "Erase memory"
    german = "Speicher löschen"
    progress = 1


class WriteFirmware(Message):
    english = "Write firmware ({0:.1f} KiB)"
    german = "Firmware schreiben ({0:.1f} KiB)"
    progress = 1


class Restart(Message):
    english = "Restart"
    german = "Neustarten"
    progress = 1
