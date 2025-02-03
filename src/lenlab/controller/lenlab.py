import logging

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.terminal import Terminal
from lenlab.message import Message
from lenlab.queued import QueuedCall

logger = logging.getLogger(__name__)


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
    ready = Signal(bool)
    reply = Signal(bytes)
    terminal_write = Signal(bytes)
    terminal_error = Signal(Message)

    def __init__(self, port_name: str, probe_timeout: int, reply_timeout: int):
        super().__init__()
        self.reply_timeout = reply_timeout
        logger.info(f"set reply timeout to {self.reply_timeout} ms")

        self.discovery = Discovery(port_name, probe_timeout)
        self.discovery.ready.connect(self.on_terminal_ready)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)

        self.lock = Lock()
        self.dac_lock = Lock()
        self.adc_lock = Lock()

        QueuedCall(self.discovery, self.discovery.find)

    @Slot(Terminal)
    def on_terminal_ready(self, terminal):
        # do not take ownership
        terminal.reply.connect(self.on_reply)
        terminal.error.connect(self.on_terminal_error)
        self.terminal_write.connect(terminal.write)
        self.terminal_error.connect(terminal.error)

        self.lock.release()
        self.dac_lock.release()
        self.adc_lock.release()
        self.ready.emit(True)

    @Slot()
    def on_terminal_error(self):
        self.timer.stop()
        self.lock.acquire()
        self.dac_lock.acquire()
        self.adc_lock.acquire()
        self.ready.emit(False)

    def send_command(self, command: bytes):
        if self.lock.acquire():
            self.timer.start(self.reply_timeout)
            self.terminal_write.emit(command)

    @Slot(bytes)
    def on_reply(self, reply):
        # ignore BSL replies
        if reply.startswith(b"L"):
            self.timer.stop()
            self.lock.release()
            self.reply.emit(reply)

    @Slot()
    def on_timeout(self):
        # a timeout may mean a broken connection and stuck buffers
        self.terminal_error.emit(NoReply())


class NoReply(Message):
    english = """No reply received from the Firmware

    The firmware may have crashed.
    Reset the firmware with the reset button on the Launchpad.
    """
    german = """Keine Antwort von der Firmware erhalten

    Die Firmware könnte abgestürzt sein.
    Resetten Sie das Launchpad mit dem Reset-Knopf.
    """
