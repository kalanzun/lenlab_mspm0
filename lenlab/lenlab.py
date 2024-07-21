from PySide6.QtCore import QObject, Slot

from lenlab.launchpad import Launchpad


class Lenlab(QObject):
    def __init__(self, launchpad: Launchpad):
        super().__init__()

        self.launchpad = launchpad
        self.launchpad.ready.connect(self.on_ready)
        self.launchpad.reply.connect(self.on_reply)

    @Slot()
    def on_ready(self) -> None:
        self.launchpad.port.setBaudRate(9600)
        self.launchpad.port.write(b"LL\x08\x00Lenlab 8.0a1")

    @Slot()
    def on_reply(self, message: bytes) -> None:
        if message[0:2] == b"LL":
            print("reply", message)
