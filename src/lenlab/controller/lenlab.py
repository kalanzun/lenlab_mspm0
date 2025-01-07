import logging
import sys

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from ..message import Message
from ..model.launchpad import find_launchpad, ti_vid
from ..model.port_info import PortInfo
from ..model.protocol import get_app_version, pack, unpack_fw_version
from . import linux
from .terminal import Terminal

logger = logging.getLogger(__name__)


class Lenlab(QObject):
    terminal: Terminal

    ready = Signal()
    error = Signal(Message)

    def __init__(self):
        super().__init__()

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.on_timeout)

    def discover(self):
        if sys.platform == "linux":
            if not linux.check_rules():
                self.error.emit(NoRules())
                return

        available_ports = PortInfo.available_ports()
        matches = find_launchpad(available_ports)
        if not matches:
            if [pi for pi in available_ports if pi.vid_pid == (ti_vid, 0xFD)]:
                self.error.emit(TivaLaunchpad())
                return

            self.error.emit(NoLaunchpad())
            return

        terminal = Terminal.from_port_info(matches[0])
        terminal.reply.connect(self.on_reply)
        terminal.error.connect(self.on_error)
        if terminal.open():
            terminal.set_baud_rate(1_000_000)
            self.terminal = terminal

            self.timer.start()
            self.terminal.write(pack(b"8ver?"))  # calls on_reply eventually

    @Slot(bytes)
    def on_reply(self, reply: bytes):
        logger.info(f"probe reply received in {self.timer.remainingTime()} ms")
        self.timer.stop()
        if reply.startswith(b"L8"):
            fw_version = unpack_fw_version(reply)
            app_version = get_app_version()
            if fw_version == app_version:
                self.ready.emit()
            else:
                self.error.emit(InvalidFirmwareVersion(fw_version, app_version))

    @Slot(Message)
    def on_error(self, error: Message):
        self.timer.stop()
        self.error.emit(error)

    @Slot()
    def on_timeout(self):
        self.error.emit(NoReply())


class NoRules(Message):
    english = "No Launchpad rules installed"


class NoLaunchpad(Message):
    english = "No Launchpad found"


class TivaLaunchpad(Message):
    english = "Tiva Launchpad found"


class NoReply(Message):
    english = "No reply received"


class InvalidFirmwareVersion(Message):
    english = "Invalid firmware version"
