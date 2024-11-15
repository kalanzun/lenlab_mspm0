from PySide6.QtCore import QObject, Signal, Slot

from ..message import Message
from ..singleshot import SingleShotTimer
from .protocol import pack
from .terminal import Terminal


class Probe(QObject):
    result = Signal(Terminal)
    error = Signal(Message)

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal
        self.unsuccessful = False

        self.timer = SingleShotTimer(self.on_timeout)

    def start(self) -> None:
        self.terminal.error.connect(self.on_error)
        self.terminal.reply.connect(self.on_reply)

        # on_error handles the error case
        if self.terminal.open():
            self.timer.start()
            self.terminal.set_baud_rate(1_000_000)
            self.terminal.write(pack(b"knock"))

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        self.timer.stop()
        self.terminal.close()
        # a terminal might send more than one error
        self.unsuccessful = True
        self.error.emit(error)

    @Slot(bytes)
    def on_reply(self, reply: bytes) -> None:
        self.timer.stop()

        if reply == pack(b"knock"):
            self.terminal.error.disconnect(self.on_error)
            self.terminal.reply.disconnect(self.on_reply)
            self.result.emit(self.terminal)
        else:
            self.terminal.close()
            self.unsuccessful = True
            self.error.emit(UnexpectedReply(self.terminal.port_name, reply))

    @Slot()
    def on_timeout(self) -> None:
        self.terminal.close()
        self.unsuccessful = True
        self.error.emit(Timeout(self.terminal.port_name))


class Discovery(QObject):
    message = Signal(Message)
    result = Signal(Terminal)
    error = Signal(Message)

    def __init__(self, probes: list[Probe]):
        super().__init__()
        self.probes = probes

    def start(self) -> None:
        for probe in self.probes:
            probe.result.connect(self.result)
            probe.error.connect(self.message)
            probe.error.connect(self.on_error)
            probe.start()

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        if all(probe.unsuccessful for probe in self.probes):
            self.error.emit(Nothing())


class UnexpectedReply(Message):
    english = "Unexpected reply on {0}: {1}"
    german = "Unerwartete Antwort auf {0}: {1}"


class Timeout(Message):
    english = "Probe timeout on {0}"
    german = "Probezeit abgelaufen auf {0}"


class Nothing(Message):
    english = "Nothing found"
    german = "Nichts gefunden"
