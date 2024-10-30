from PySide6.QtCore import QObject, Signal, Slot

from .bsl import BSL
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

        self.firmware_timer = SingleShotTimer(self.on_firmware_timeout, timeout=300)
        self.bsl_timer = SingleShotTimer(self.on_bsl_timeout, timeout=300)

    def start(self) -> None:
        self.terminal.ack.connect(self.on_ack)
        self.terminal.error.connect(self.on_error)
        self.terminal.reply.connect(self.on_reply)

        # on_error handles the error case
        if self.terminal.open():
            self.terminal.set_baud_rate(1_000_000)
            self.firmware_timer.start()
            self.terminal.write(Protocol.knock_packet)

    @Slot(str)
    def on_error(self, error: str) -> None:
        self.firmware_timer.stop()
        self.bsl_timer.stop()

        self.error.emit(error)

    @Slot(bytes)
    def on_ack(self, ack: bytes) -> None:
        self.firmware_timer.stop()
        self.bsl_timer.stop()

        if ack == b"\x00":
            self.terminal.bsl = True
            self.result.emit(self.terminal)
        else:
            self.terminal.close()
            self.error.emit(f"unexpected ack {ack}")

    @Slot(bytes)
    def on_reply(self, reply: bytes) -> None:
        self.firmware_timer.stop()
        self.bsl_timer.stop()

        if reply == Protocol.knock_packet:
            self.terminal.firmware = True
            self.result.emit(self.terminal)
        elif reply == BSL.ok_packet:
            self.terminal.bsl = True
            self.result.emit(self.terminal)
        else:
            self.terminal.close()
            self.error.emit(f"unexpected reply {reply}")

    @Slot()
    def on_firmware_timeout(self) -> None:
        self.terminal.set_baud_rate(9_600)
        self.bsl_timer.start()
        self.terminal.write(BSL.connect_packet)

    @Slot()
    def on_bsl_timeout(self) -> None:
        self.terminal.close()
        self.error.emit("discovery timeout")
