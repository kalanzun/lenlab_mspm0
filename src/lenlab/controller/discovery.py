from PySide6.QtCore import QObject, Signal

from ..message import Message
from ..model.launchpad import find_launchpad, ti_vid, tiva_pid
from ..model.port_info import PortInfo
from .terminal import Terminal


class Discovery(QObject):
    available_terminals: list[Terminal]
    terminal: Terminal | None

    error = Signal(Message)
    ready = Signal()

    def __init__(self):
        super().__init__()

        self.available_terminals = []
        self.terminal = None

    def discover(self, available_ports: list[PortInfo], select_first: bool = False):
        matches = find_launchpad(available_ports)
        if not matches:
            if any(True for pi in available_ports if pi.vid == ti_vid and pi.pid == tiva_pid):
                self.error.emit(TivaLaunchpad())
                return

            self.error.emit(NoLaunchpad())
            return

        if select_first:
            del matches[1:]

        self.available_terminals = [Terminal(match) for match in matches]


class NoLaunchpad(Message):
    english = "No Launchpad found"


class TivaLaunchpad(Message):
    english = "Tiva Launchpad found"
