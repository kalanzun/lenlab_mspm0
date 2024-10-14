from importlib import metadata

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from .launchpad import Launchpad
from .message import Message


def pad(seq, n):
    for x in seq:
        yield x
        n -= 1
    assert n >= 0
    for _ in range(n):
        yield 0


class Lenlab(QObject):
    ready = Signal()
    error = Signal(Message)

    def __init__(self, launchpad: Launchpad):
        super().__init__()

        self.launchpad = launchpad
        self.launchpad.ready.connect(self.on_ready)
        self.launchpad.reply.connect(self.on_reply)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)

    def command(self, payload: bytes = b"") -> None:
        length = len(payload)
        assert length >= 5

        length = length - 4  # implicit 4 bytes payload (BSL checksum)
        assert length <= 32

        packet = bytes().join(
            [
                b"L",
                length.to_bytes(2, byteorder="little"),
                payload,
            ]
        )
        print(packet)
        self.launchpad.port.write(packet)

    @Slot()
    def on_ready(self) -> None:
        self.launchpad.port.setBaudRate(4_000_000)
        self.command(b"8ver?")
        self.timer.start(200)  # less is too short sometimes

    @Slot()
    def on_reply(self, packet: bytes) -> None:
        self.timer.stop()
        major, dot, *rest = metadata.version("lenlab").encode("ascii")
        assert dot == ord(".")
        pattern = b"L" + (1).to_bytes(2, "little") + bytes([major]) + bytes(pad(rest, 4))
        print(f"Lenlab version {pattern}")
        print(f"Reply {packet}")
        if packet == pattern:
            self.ready.emit()
        else:
            version = f"{chr(packet[3])}.{''.join(chr(x) for x in packet[4:] if x)}"
            self.error.emit(InvalidFirmwareVersion(version, metadata.version("lenlab")))

    @Slot()
    def on_timeout(self) -> None:
        self.error.emit(NoFirmware())


class NoFirmware(Message):
    english = """No reply from the Launchpad
        Lenlab requires the Lenlab firmware on the Launchpad.
        Please write the firmware on the Launchpad with the Programmer."""
    german = """Keine Antwort vom Launchpad
        Lenlab benötigt die Lenlab-Firmware auf dem Launchpad.
        Bitte die Firmware mit dem Programmierer auf das Launchpad schreiben."""


class InvalidFirmwareVersion(Message):
    english = """Invalid firmware version: {0}
        This Lenlab requires version {1}.
        Please write the current version to the Launchpad with the Programmer."""
    german = """Ungültige Firmware-Version: {0}
        Dieses Lenlab benötigt Version {1}.
        Bitte die aktuelle Version mit dem Programmierer auf das Launchpad schreiben."""
