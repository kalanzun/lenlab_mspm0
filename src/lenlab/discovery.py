from PySide6.QtCore import QObject, Signal, Slot

from .message import Message
from .protocol import Protocol
from .singleshot import SingleShotTimer
from .terminal import Terminal


class Probe(QObject):
    result = Signal(Terminal)
    error = Signal(Message)

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal

        self.timer = SingleShotTimer(self.on_timeout, timeout=300)

    def start(self) -> None:
        self.terminal.error.connect(self.on_error)
        self.terminal.reply.connect(self.on_reply)

        # on_error handles the error case
        if self.terminal.open():
            self.terminal.set_baud_rate(Protocol.baud_rate)
            self.terminal.write(Protocol.knock_packet)
            self.timer.start()

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        self.timer.stop()
        self.error.emit(error)

    @Slot(bytes)
    def on_reply(self, reply: bytes) -> None:
        self.timer.stop()

        if reply == Protocol.knock_packet:
            self.terminal.error.disconnect(self.on_error)
            self.terminal.reply.disconnect(self.on_reply)
            self.result.emit(self.terminal)
        else:
            self.terminal.close()
            self.error.emit(UnexpectedReply(self.terminal.port_name, reply))

    @Slot()
    def on_timeout(self) -> None:
        self.terminal.close()
        self.error.emit(Timeout(self.terminal.port_name))


class Discovery(QObject):
    message = Signal(Message)
    result = Signal(Terminal)
    error = Signal(Message)

    def __init__(self, probes: list[Probe]):
        super().__init__()
        self.probes = probes
        self.count = len(self.probes)

    def start(self) -> None:
        for probe in self.probes:
            probe.result.connect(self.result)
            probe.error.connect(self.message)
            probe.error.connect(self.on_error)
            probe.start()

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        self.count -= 1
        if self.count == 0:
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
