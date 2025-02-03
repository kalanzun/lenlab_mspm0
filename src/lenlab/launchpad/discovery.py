import logging
import sys
from typing import cast

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from ..message import Message
from ..queued import QueuedCall
from . import rules
from .launchpad import find_launchpad, find_tiva_launchpad
from .port_info import PortInfo
from .protocol import command, get_app_version, unpack_fw_version
from .terminal import Terminal

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
        self.terminal.ack_mode = False
        self.terminal.write(command(b"8"))

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
    available = Signal()  # terminals available for programming or probing
    ready = Signal(Terminal)  # firmware connection established
    error = Signal(Message)

    terminals: list[Terminal]
    probes: list[Probe]

    def __init__(self, port_name: str = "", probe_timeout: int = 600):
        super().__init__()
        self.port_name = port_name
        self.probe_timeout = probe_timeout
        logger.info(f"set probe timeout to {probe_timeout} ms")

        self.terminals = []
        self.probes = []

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.probe_timeout)
        self.timer.timeout.connect(self.stop)
        self.timer.timeout.connect(self.on_timeout)

        self.available.connect(self.log_available)
        self.error.connect(logger.error)
        self.ready.connect(self.log_ready)

    @Slot()
    def log_available(self):
        logger.info(f"available {', '.join(t.port_name for t in self.terminals)}")

    @Slot(Terminal)
    def log_ready(self, terminal):
        logger.info(f"terminal {terminal.port_name} ready")

    @Slot()
    def retry(self):
        logger.info("retry")
        if self.terminals:
            self.probe()
        else:
            self.find()

    @Slot()
    def find(self):
        logger.info("find")

        if sys.platform == "linux":
            if not rules.check_rules():
                self.error.emit(NoRules())
                return

        if self.port_name:
            pi = PortInfo.from_name(self.port_name)
            if pi.is_available:
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
        QueuedCall(self, self.open)

    @Slot()
    def open(self):
        for terminal in self.terminals:
            terminal.error.connect(self.stop)
            terminal.error.connect(self.on_terminal_error)

            # on_error handles the error message and cleanup
            if not terminal.open():
                return

        self.available.emit()
        QueuedCall(self, self.probe)

    @Slot()
    def probe(self):
        self.timer.start()
        self.probes = [Probe(terminal) for terminal in self.terminals]
        for probe in self.probes:
            probe.select.connect(self.stop)
            probe.select.connect(self.select_terminal)
            probe.ready.connect(self.ready.emit)
            probe.error.connect(self.error.emit)
            probe.start()

    @Slot()
    def stop(self):
        self.timer.stop()
        for probe in self.probes:
            probe.deleteLater()

        self.probes = []

    @Slot(Message)
    def on_terminal_error(self, error):
        terminal = cast(Terminal, self.sender())

        logger.info(f"close on error {terminal.port_name}")
        terminal.close()
        terminal.deleteLater()

        self.terminals = [t for t in self.terminals if t is not terminal]
        self.error.emit(error)

    @Slot(Terminal)
    def select_terminal(self, terminal):
        logger.info(f"select {terminal.port_name}")

        for t in self.terminals:
            if t is not terminal:
                t.close()
                t.deleteLater()

        self.terminals = [terminal]

    @Slot()
    def on_timeout(self):
        logger.info("timeout")
        self.error.emit(NoFirmware())


class NoLaunchpad(Message):
    english = """No Launchpad found

    Connect the Launchpad via USB to your computer.
    """
    german = """Kein Launchpad gefunden

    Verbinden Sie das Launchpad über USB mit Ihrem Computer.
    """


class NotFound(NoLaunchpad):
    english = """Port {0} not found

    The system does not know about a port "{0}".
    """
    german = """Port {0} nicht gefunden

    Das System kennt keinen Port "{0}".
    """


class TivaLaunchpad(NoLaunchpad):
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


class NoRules(NoLaunchpad):
    english = """No Launchpad rules installed

    The Launchpad rules prevent a program called ModemManager
    to connect to and block the Launchpad.

    Disconnect the Launchpad from the computer and click on "Install rules" in the Lenlab menu.
    This action requests super user access.
    """
    german = """Keine Launchpad-Regeln installiert

    Die Launchpad-Regeln verbieten einem Programms namens ModemManager
    den Verbindungsaufbau und die Blockade des Launchpads.

    Trennen Sie das Launchpad vom Computer
    und klicken Sie auf "Regeln installieren" im Lenlab-Menü.
    Diese Aktion fordert Zugriffsberechtigung als Administrator an. 
    """


class NoFirmware(Message):
    english = """No reply received from the Launchpad

    Lenlab requires the Lenlab firmware on the Launchpad.
    Write the firmware on the Launchpad with the Programmer.
    """
    german = """Keine Antwort vom Launchpad erhalten

    Lenlab benötigt die Lenlab-Firmware auf dem Launchpad.
    Schreiben Sie die Firmware mit dem Programmierer auf das Launchpad.
    """


class InvalidVersion(NoFirmware):
    english = """Invalid firmware version: {0}

    This Lenlab requires version {1}.
    Write the current version to the Launchpad with the Programmer.
    """
    german = """Ungültige Firmware-Version: {0}

    Dieses Lenlab benötigt Version {1}.
    Schreiben Sie die aktuelle Version mit dem Programmierer auf das Launchpad.
    """


class InvalidReply(NoFirmware):
    english = """Invalid firmware version

    This Lenlab requires version {0}.
    Write the current version to the Launchpad with the Programmer.
    """
    german = """Ungültige Firmware-Version

    Dieses Lenlab benötigt Version {0}.
    Schreiben Sie die aktuelle Version mit dem Programmierer auf das Launchpad.
    """
