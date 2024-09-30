from importlib import metadata

from PySide6.QtCore import QObject, Slot, Signal

from lenlab.launchpad import Launchpad


def pad(seq, n):
    for x in seq:
        yield x
        n -= 1
    assert n >= 0
    for _ in range(n):
        yield 0


class Lenlab(QObject):
    ready = Signal()

    def __init__(self, launchpad: Launchpad):
        super().__init__()

        self.launchpad = launchpad
        self.launchpad.ready.connect(self.on_ready)
        self.launchpad.reply.connect(self.on_reply)

    @Slot()
    def on_ready(self) -> None:
        self.launchpad.port.setBaudRate(4_000_000)
        self.launchpad.port.write(b"L8\x00\x00lab!")

    @Slot()
    def on_reply(self, message: bytes) -> None:
        major, dot, *rest = metadata.version("lenlab").encode("ascii")
        assert dot == ord(".")
        pattern = b"L" + bytes([major]) + bytes([0, 0]) + bytes(pad(rest, 4))
        print(f"Lenlab version {pattern}")
        print(f"Reply {message}")
        if message == pattern:
            self.ready.emit()
