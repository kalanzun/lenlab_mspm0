from PySide6.QtCore import QObject, Signal, Slot

from ..launchpad.discovery import Discovery
from ..launchpad.terminal import Terminal
from ..message import Message


class Lenlab(QObject):
    error = Signal(Message)
    new_terminal = Signal(Terminal)

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
        self.terminal.error.connect(self.on_terminal_error)
        del self.discovery
        self.new_terminal.emit(terminal)

    def remove_terminal(self):
        if hasattr(self, "terminal"):
            self.terminal.close()
            self.terminal.error.disconnect(self.on_terminal_error)
            del self.terminal

    @Slot(Message)
    def on_terminal_error(self, message: Message):
        self.error.emit(message)
        self.terminal.error.disconnect(self.on_terminal_error)
        del self.terminal
