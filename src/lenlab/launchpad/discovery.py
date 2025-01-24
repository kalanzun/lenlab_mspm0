import logging
import sys
from typing import cast

from attrs import frozen
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot

from ..message import Message
from . import linux
from .launchpad import find_launchpad, find_tiva_launchpad
from .port_info import PortInfo
from .protocol import get_app_version, pack, unpack_fw_version
from .terminal import FirmwareError, LaunchpadError, Terminal

logger = logging.getLogger(__name__)


class Discovery(QObject):
    available = Signal()  # terminals available for programming or probing
    ready = Signal(Terminal)  # firmware (correct version) connection established
    error = Signal(Message)

    port_name: str
    interval: int = 600

    terminals: list[Terminal]

    def __init__(self, port_name: str = ""):
        super().__init__()

        self.port_name = port_name
        self.terminals = []

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.on_timeout)

        self.available.connect(self.log_available)
        self.available.connect(self.probe, Qt.ConnectionType.QueuedConnection)
        self.error.connect(logger.error)
        self.ready.connect(self.log_ready)

    @Slot()
    def log_available(self):
        logger.info(f"{', '.join(t.port_name for t in self.terminals)} available")

    @Slot(Terminal)
    def log_ready(self, terminal):
        logger.info(f"terminal {terminal.port_name} ready")

    def retry(self):
        logger.info("retry")
        if self.terminals:
            self.log_available()
            self.probe()
        else:
            self.find()

    @Slot()
    def find(self):
        logger.info("find")

        if sys.platform == "linux":
            if not linux.check_rules():
                self.error.emit(NoRules())
                return

        if self.port_name:
            pi = PortInfo.from_name(self.port_name)
            if pi:
                matches = [pi]
            else:
                self.error.emit(NotFound(self.port_name))
                return

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
        logger.info("probe")
        self.timer.start()
        for terminal in self.terminals:
            terminal.reply.connect(self.on_reply)
            terminal.error.connect(self.on_error)
            terminal.closed.connect(self.on_closed)

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

        app_version = get_app_version()
        if fw_version := unpack_fw_version(reply):
            if fw_version == app_version:
                self.ready.emit(terminal)
            else:
                self.error.emit(InvalidVersion(fw_version, app_version))

        else:
            self.error.emit(InvalidReply(app_version))

    @Slot(Message)
    def on_error(self, error):
        if not self.timer.isActive():
            return

        self.timer.stop()
        self.error.emit(error)

    @Slot()
    def on_closed(self):
        self.terminals = [terminal for terminal in self.terminals if terminal.is_open]

    @Slot()
    def on_timeout(self):
        self.error.emit(NoFirmware())


@frozen
class NoLaunchpad(LaunchpadError):
    english = """No Launchpad found
    
    Connect the Launchpad via USB to your computer.
    """
    german = """Kein Launchpad gefunden
    
    Verbinden Sie das Launchpad über USB mit Ihrem Computer.
    """


@frozen
class NotFound(LaunchpadError):
    port_name: str
    english = """Port {port_name} not found
    
    The system does not know about a port "{port_name}".
    """
    german = """Port {port_name} nicht gefunden
    
    Das System kennt keinen Port "{port_name}".
    """


@frozen
class TivaLaunchpad(LaunchpadError):
    english = """Tiva C-Series Launchpad found
    
    This Lenlab Version 8 works with the Launchpad LP-MSPM0G3507.
    Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
    works with the Tiva C-Series Launchpad EK-TM4C123GXL.
    """
    german = """Tiva C-Serie Launchpad gefunden
    
    Dieses Lenlab in Version 8 funktioniert mit dem Launchpad LP-MSPM0G3507.
    Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
    funktioniert mit dem Tiva C-Serie Launchpad EK-TM4C123GXL.
    """


@frozen
class NoRules(LaunchpadError):
    english = """No Launchpad rules installed
    
    The Launchpad rules prevent a program called ModemManager
    to connect to the Launchpad and block Lenlab.

    Disconnect the Launchpad from the computer and install the Launchpad rules.
    This action asks for super user access.
    """
    german = """Keine Launchpad-Regeln installiert
    
    Die Launchpad-Regeln verbieten einem Programms namens ModemManager
    den Verbindungsaufbau mit dem Launchpad und die Blockade Lenlabs.

    Trennen Sie das Launchpad vom Computer und installieren Sie die Launchpad-Regeln.
    Diese Aktion fragt nach Administratorzugriff. 
    """


@frozen
class NoFirmware(FirmwareError):
    english = """No reply received from the Launchpad
    
    Lenlab requires the Lenlab firmware on the Launchpad.
    Write the firmware on the Launchpad with the Programmer.
    """
    german = """Keine Antwort vom Launchpad erhalten
    
    Lenlab benötigt die Lenlab-Firmware auf dem Launchpad.
    Schreiben Sie die Firmware mit dem Programmierer auf das Launchpad.
    """


@frozen
class InvalidVersion(FirmwareError):
    fw_version: str
    app_version: str
    english = """Invalid firmware version: {fw_version}

    This Lenlab requires version {app_version}.
    Write the current version to the Launchpad with the Programmer.
    """
    german = """Ungültige Firmware-Version: {fw_version}

    Dieses Lenlab benötigt Version {app_version}.
    Schreiben Sie die aktuelle Version mit dem Programmierer auf das Launchpad.
    """


@frozen
class InvalidReply(FirmwareError):
    app_version: str
    english = """Invalid firmware version

    This Lenlab requires version {app_version}.
    Write the current version to the Launchpad with the Programmer.
    """
    german = """Ungültige Firmware-Version

    Dieses Lenlab benötigt Version {app_version}.
    Schreiben Sie die aktuelle Version mit dem Programmierer auf das Launchpad.
    """
