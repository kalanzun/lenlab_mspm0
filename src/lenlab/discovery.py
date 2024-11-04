from PySide6.QtCore import QObject, Signal, Slot

from .protocol import Protocol
from .singleshot import SingleShotTimer
from .terminal import Terminal


class Future(QObject):
    error = Signal(str)
    result = Signal(QObject)


class Discovery(Future):
    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal

        self.timer = SingleShotTimer(self.on_timeout, timeout=300)

    def start(self) -> None:
        self.terminal.error.connect(self.on_error)
        self.terminal.reply.connect(self.on_reply)

        # on_error handles the error case
        if self.terminal.open():
            self.terminal.set_baud_rate(1_000_000)
            self.timer.start()
            self.terminal.write(Protocol.knock_packet)

    @Slot(str)
    def on_error(self, error: str) -> None:
        self.timer.stop()
        self.error.emit(error)

    @Slot(bytes)
    def on_reply(self, reply: bytes) -> None:
        self.timer.stop()

        if reply == Protocol.knock_packet:
            self.terminal.firmware = True
            self.result.emit(self.terminal)
        else:
            self.terminal.close()
            self.error.emit(f"unexpected reply {reply}")

    @Slot()
    def on_timeout(self) -> None:
        self.terminal.close()
        self.error.emit("discovery timeout")
