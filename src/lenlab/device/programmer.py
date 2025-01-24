from importlib import resources

from PySide6.QtCore import Signal, Slot

import lenlab
from lenlab.launchpad.bsl import BootstrapLoader
from lenlab.launchpad.terminal import Terminal
from lenlab.message import Message

from .device import Device


class Programmer(Device):
    message = Signal(Message)
    success = Signal(Terminal)
    error = Signal(Message)

    bootstrap_loaders: list[BootstrapLoader]
    n_messages: int = 8

    @Slot()
    def start(self):
        self.bootstrap_loaders = [
            BootstrapLoader(terminal) for terminal in self.lenlab.discovery.terminals
        ]
        firmware = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()

        for bsl in self.bootstrap_loaders:
            bsl.message.connect(self.message)
            bsl.success.connect(self.on_success)
            bsl.error.connect(self.message)
            bsl.error.connect(self.on_error)
            bsl.start(firmware)

    @Slot(Terminal)
    def on_success(self, terminal):
        self.bootstrap_loaders = []
        self.success.emit(terminal)
        self.lenlab.discovery.select_terminal(terminal)
        self.lenlab.discovery.retry()

    @Slot()
    def on_error(self):
        if all(bsl.unsuccessful for bsl in self.bootstrap_loaders):
            self.bootstrap_loaders = []
            self.error.emit(ProgrammingFailed())


class ProgrammingFailed(Message):
    link = """[https://pypi.org/project/lenlab/](https://pypi.org/project/lenlab/)"""

    english = f"""Programming failed

    Maybe the "Bootstrap Loader" did not start?
    Please try the reset procedure (buttons S1 + RESET) once more.
    The red LED at the bottom edge shall be off.

    If programming still does not work, you can try to power off the launchpad
    (unplug USB connection and plug it back in) and to restart the computer.
    Otherwise, you can try TI UniFlash (Manual {link})"""

    german = f"""Programmieren fehlgeschlagen

    Vielleicht startete der "Bootstrap Loader" nicht?
    Versuchen Sie die Reset-Prozedur (Tasten S1 + RESET) noch einmal.
    Die rote LED an der Unterkante soll aus sein.

    Wenn das Programmieren trotzdem nicht funktioniert können Sie das Launchpad stromlos schalten
    (USB-Verbindung ausstecken und wieder anstecken) und den Computer neustarten.
    Ansonsten können Sie TI UniFlash ausprobieren (Anleitung {link})"""
