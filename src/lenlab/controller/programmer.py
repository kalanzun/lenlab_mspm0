from importlib import resources

from PySide6.QtCore import QObject, Signal, Slot

import lenlab

from ..launchpad.bsl import BootstrapLoader
from ..launchpad.discovery import Discovery
from ..launchpad.terminal import Terminal
from ..message import Message
from ..queued import QueuedCall


class Programmer(QObject):
    message = Signal(Message)
    success = Signal(Message)
    error = Signal(Message)

    bootstrap_loaders: list[BootstrapLoader]
    n_messages: int = 8

    def __init__(self, discovery: Discovery):
        super().__init__()

        self.autostart = False
        self.discovery = discovery
        self.discovery.available.connect(self.on_discovery_available)
        self.discovery.error.connect(self.on_discovery_error)

    def start(self):
        if self.discovery.terminals:
            self.program()

        else:
            self.autostart = True
            self.discovery.probe_enabled = False
            self.discovery.find()

    @Slot()
    def on_discovery_available(self):
        if self.autostart:
            self.autostart = False
            self.program()

    @Slot(Message)
    def on_discovery_error(self, message: Message):
        if self.autostart:
            self.autostart = False
            self.message.emit(NoTerminalAvailable())
            self.error.emit(ProgrammingFailed())

    def program(self):
        firmware = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

        self.bootstrap_loaders = [
            BootstrapLoader(terminal) for terminal in self.discovery.terminals
        ]

        for bsl in self.bootstrap_loaders:
            bsl.message.connect(self.message)
            bsl.success.connect(self.on_success)
            bsl.error.connect(self.message)
            bsl.error.connect(self.on_error)
            bsl.start(firmware)

    def stop(self):
        for bsl in self.bootstrap_loaders:
            bsl.deleteLater()

        self.bootstrap_loaders = []

    @Slot(Terminal)
    def on_success(self, terminal):
        self.success.emit(ProgrammingSuccessful())
        self.stop()

        self.discovery.select_terminal(terminal)
        QueuedCall(self.discovery, self.discovery.retry)

    @Slot()
    def on_error(self):
        if all(bsl.unsuccessful for bsl in self.bootstrap_loaders):
            self.error.emit(ProgrammingFailed())
            self.stop()


class ProgrammingSuccessful(Message):
    english = """Programming successful

    The programmer wrote the Lenlab firmware to the Launchpad.
    Lenlab should be connected and ready for measurements."""

    german = """Programmieren erfolgreich

    Der Programmierer schrieb die Lenlab Firmware auf das Launchpad.
    Lenlab sollte verbunden sein und bereit für Messungen."""


class ProgrammingFailed(Message):
    english = """Programming failed

    Maybe the "Bootstrap Loader" did not start?
    Please try the reset procedure (buttons S1 + RESET) once more.
    The red LED at the bottom edge shall be off.

    If programming still does not work, you can try to power off the launchpad
    (unplug USB connection and plug it back in) and click retry on the Launchpad error message.
    Otherwise, you can try TI UniFlash ([Instructions](about))"""

    german = """Programmieren fehlgeschlagen

    Vielleicht startete der "Bootstrap Loader" nicht?
    Versuchen Sie die Reset-Prozedur (Tasten S1 + RESET) noch einmal.
    Die rote LED an der Unterkante soll aus sein.

    Wenn das Programmieren trotzdem nicht funktioniert können Sie das Launchpad stromlos schalten
    (USB-Verbindung ausstecken und wieder anstecken)
    und auf neuen Versuch in der Launchpad-Fehlermeldung klicken.
    Ansonsten können Sie TI UniFlash ([Anleitung](about)) ausprobieren"""


class NoTerminalAvailable(Message):
    english = "No Launchpad connected"
    german = "Kein Launchpad verbunden"
