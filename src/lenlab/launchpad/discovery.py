import logging
import sys

from attrs import frozen
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot

from ..message import Message
from . import linux
from .launchpad import find_launchpad, find_tiva_launchpad
from .port_info import PortInfo
from .protocol import get_app_version, pack, unpack_fw_version
from .terminal import LaunchpadError, Terminal

logger = logging.getLogger(__name__)


class Probe(QObject):
    select = Signal(Terminal)
    ready = Signal(Terminal)
    error = Signal(Message)

    def __init__(self, terminal: Terminal):
        super().__init__()
        self.terminal = terminal

    def start(self):
        logger.info(f"probe {self.terminal.port_name}")

        # disconnects automatically when the probe is destroyed
        self.terminal.reply.connect(self.on_reply)

        self.terminal.set_baud_rate(1_000_000)
        self.terminal.write(pack(b"8ver?"))

    @Slot(bytes)
    def on_reply(self, reply):
        # now we know which terminal talks to the firmware
        self.select.emit(self.terminal)

        # the select signal with argument avoids a sender() call in the signal handler,
        # which would be inconvenient to test

        app_version = get_app_version()
        if fw_version := unpack_fw_version(reply):
            if fw_version == app_version:
                self.ready.emit(self.terminal)
            else:
                self.error.emit(InvalidVersion(fw_version, app_version))

        else:
            self.error.emit(InvalidReply(app_version))


class Discovery(QObject):
    found = Signal()
    available = Signal()  # terminals available for programming or probing
    ready = Signal(Terminal)  # firmware (correct version) connection established
    error = Signal(Message)

    port_name: str
    interval: int = 600

    terminals: list[Terminal]
    probes: list[Probe]

    def __init__(self, port_name: str = ""):
        super().__init__()

        self.port_name = port_name
        self.terminals = []
        self.probes = []

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.on_timeout)

        self.found.connect(self.open, Qt.ConnectionType.QueuedConnection)
        self.available.connect(self.log_available)
        self.available.connect(self.probe, Qt.ConnectionType.QueuedConnection)
        self.error.connect(logger.error)
        self.ready.connect(self.log_ready)

    @Slot()
    def log_available(self):
        logger.info(f"available {', '.join(t.port_name for t in self.terminals)}")

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
        self.found.emit()

    @Slot()
    def open(self):
        for terminal in self.terminals:
            terminal.error.connect(self.on_terminal_error)

            # on_error handles the error message and cleanup
            if not terminal.open():
                return

        self.available.emit()

    @Slot()
    def probe(self):
        self.timer.start()
        self.probes = [Probe(terminal) for terminal in self.terminals]
        for probe in self.probes:
            probe.select.connect(self.on_probe_select)
            probe.ready.connect(self.ready.emit)
            probe.error.connect(self.error.emit)
            probe.start()

    @Slot(Message)
    def on_terminal_error(self, error):
        self.timer.stop()
        self.probes = []
        self.terminals = [terminal for terminal in self.terminals if terminal.is_open]
        self.error.emit(error)

    @Slot(Terminal)
    def on_probe_select(self, terminal: Terminal):
        self.timer.stop()
        self.probes = []

        logger.info(f"select {terminal.port_name}")

        for t in self.terminals:
            if t is not terminal:
                t.close()

        self.terminals = [terminal]

    @Slot()
    def on_timeout(self):
        self.probes = []
        logger.info("timeout")
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
class FirmwareError(Message):
    pass


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
