from PySide6.QtCore import QObject, QTimer, Signal, Slot

from ..model.launchpad import ti_pid, ti_vid
from ..model.message import Message
from ..model.port_info import PortInfo
from ..model.protocol import get_app_version, pack, unpack_fw_version
from .terminal import Terminal


def find_launchpad(port_infos: list[PortInfo]) -> list[PortInfo]:
    # vid, pid
    port_infos = [pi for pi in port_infos if pi.vid_pid == (ti_vid, ti_pid)]

    # cu*
    if matches := [pi for pi in port_infos if pi.name.startswith("cu")]:
        port_infos = matches

    # sort by number
    port_infos.sort(key=lambda pi: pi.sort_key)

    return port_infos


class Probe(QObject):
    error = Signal(Message)
    success = Signal()

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.on_timeout)

    def probe(self):
        self.terminal.reply.connect(self.on_reply)
        self.terminal.error.connect(self.on_error)

        self.terminal.write(pack(b"8ver?"))
        self.timer.start()

    @Slot(bytes)
    def on_reply(self, reply: bytes):
        self.timer.stop()

        fw_version = unpack_fw_version(reply)
        app_version = get_app_version()
        if fw_version == app_version:
            self.terminal.reply.disconnect(self.on_reply)
            self.terminal.error.disconnect(self.on_error)
            self.success.emit()
        else:
            self.error.emit(InvalidFirmwareVersion(fw_version, app_version))

    @Slot(Message)
    def on_error(self, error: Message):
        self.error.emit(error)

    @Slot()
    def on_timeout(self):
        self.error.emit(NoReply())


class InvalidFirmwareVersion(Message):
    english = """Invalid firmware version: {0}

    This Lenlab requires version {1}.
    Write the current version to the Launchpad with the Programmer."""

    german = """Ungültige Firmware-Version: {0}

    Dieses Lenlab benötigt Version {1}.
    Schreiben Sie die aktuelle Version mit dem Programmierer auf das Launchpad."""


class NoReply(Message):
    english = """No reply from the Launchpad

    Lenlab requires the Lenlab firmware on the Launchpad.
    Write the firmware to the Launchpad with the Programmer."""

    german = """Keine Antwort vom Launchpad

    Lenlab benötigt die Lenlab-Firmware auf dem Launchpad.
    Schreiben Sie die Firmware mit dem Programmierer auf das Launchpad."""
