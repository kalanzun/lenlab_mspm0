from PySide6.QtCore import QObject, Signal, Slot

from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.terminal import Terminal
from lenlab.message import Message
from lenlab.queued import QueuedCall


class Lock(QObject):
    locked = Signal(bool)

    def __init__(self):
        super().__init__()
        self.is_locked = True

    def acquire(self) -> bool:
        if self.is_locked:
            return False

        self.is_locked = True
        self.locked.emit(True)
        return True

    def release(self):
        self.is_locked = False
        self.locked.emit(False)


class Lenlab(QObject):
    reply = Signal(bytes)
    write = Signal(bytes)

    def __init__(self):
        super().__init__()
        self.discovery = Discovery()
        self.discovery.ready.connect(self.on_terminal_ready)

        self.lock = Lock()
        self.dac_lock = Lock()
        self.adc_lock = Lock()

        QueuedCall(self.discovery, self.discovery.find)

    @Slot(Terminal)
    def on_terminal_ready(self, terminal):
        # do not take ownership
        terminal.reply.connect(self.on_reply)
        terminal.error.connect(self.on_terminal_error)
        self.write.connect(terminal.write)

        self.lock.release()
        self.dac_lock.release()
        self.adc_lock.release()

    @Slot(Message)
    def on_terminal_error(self, error):
        self.lock.acquire()
        self.dac_lock.acquire()
        self.adc_lock.acquire()

    def send_command(self, command: bytes):
        if self.lock.acquire():
            self.write.emit(command)

    def on_reply(self, reply: bytes):
        # ignore BSL replies
        if reply.startswith(b"L"):
            self.lock.release()
            self.reply.emit(reply)
