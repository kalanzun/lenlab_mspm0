import logging
import sys
from typing import cast

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from .launchpad import find_launchpad, find_tiva_launchpad
from .port_info import PortInfo
from .protocol import get_app_version, pack, unpack_fw_version
from .terminal import Terminal

logger = logging.getLogger(__name__)


class Discovery(QObject):
    available = Signal()  # terminals available for programming or probing
    ready = Signal(Terminal)  # firmware (correct version) connection established
    error = Signal(Exception)

    port: str
    interval: int = 600

    terminals: list[Terminal]

    def __init__(self, port: str = ""):
        super().__init__()

        self.port = port
        self.terminals = []

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.on_timeout)

    @Slot()
    def find(self):
        if self.port:
            matches = [PortInfo.from_name(self.port)]
        else:
            available_ports = PortInfo.available_ports()
            matches = find_launchpad(available_ports)
            if not matches:
                if find_tiva_launchpad(available_ports):
                    self.error.emit(TivaLaunchpad())
                    return

                self.error.emit(NoLaunchpad())
                return

            if sys.platform != "win32":
                del matches[1:]

        self.terminals = [Terminal.from_port_info(pi) for pi in matches]
        self.available.emit()

    @Slot()
    def probe(self):
        self.timer.start()
        for terminal in self.terminals:
            terminal.reply.connect(self.on_reply)
            terminal.error.connect(self.on_error)

            # on_error handles the error message
            if not terminal.open():
                break

            terminal.set_baud_rate(1_000_000)
            terminal.write(pack(b"8ver?"))

    @Slot(bytes)
    def on_reply(self, reply):
        if not self.timer.isActive():
            return

        self.timer.stop()

        # now we know which terminal talks to the firmware
        terminal = cast(Terminal, self.sender())
        self.terminals = [terminal]

        if fw_version := unpack_fw_version(reply):
            app_version = get_app_version()
            if fw_version == app_version:
                self.ready.emit(terminal)
            else:
                self.error.emit(InvalidFirmwareVersion(fw_version, app_version))

        else:
            self.error.emit(InvalidReply())

    @Slot(Exception)
    def on_error(self, error):
        if not self.timer.isActive():
            return

        self.timer.stop()
        self.error.emit(error)

    @Slot()
    def on_timeout(self):
        self.error.emit(NoFirmware())


class TivaLaunchpad(Exception):
    pass


class NoLaunchpad(Exception):
    pass


class InvalidFirmwareVersion(Exception):
    pass


class InvalidReply(Exception):
    pass


class NoFirmware(Exception):
    pass
