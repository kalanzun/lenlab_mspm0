from PySide6.QtCore import QObject, Signal, Slot

from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.terminal import Terminal
from lenlab.message import Message


class Lenlab(QObject):
    error = Signal(Message)
    ready = Signal(Terminal)

    discovery: Discovery
    terminal: Terminal

    def retry(self):
        self.discovery = Discovery()
        self.discovery.error.connect(self.error)
        self.discovery.result.connect(self.on_result)
        self.discovery.discover()

    @Slot(Terminal)
    def on_result(self, terminal: Terminal):
        self.terminal = terminal
        del self.discovery
        self.ready.emit(terminal)
