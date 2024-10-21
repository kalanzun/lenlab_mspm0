from importlib.resources import is_resource, read_binary
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .bsl import BootstrapLoader
from .figure import LaunchpadFigure
from .message import Message
from .terminal import Terminal


class Programmer(QWidget):
    title = "Programmer"
    # description = "MSPM0 flash programming tool"

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal

        self.bsl = BootstrapLoader(self.terminal)
        self.bsl.message.connect(self.on_message)
        self.bsl.finished.connect(self.on_finished)

        layout = QHBoxLayout()
        self.setLayout(layout)

        program_layout = QVBoxLayout()
        layout.addLayout(program_layout)

        self.program_button = QPushButton("Program")
        program_layout.addWidget(self.program_button)
        # self.program_button.setEnabled(False)
        self.program_button.clicked.connect(self.on_program_clicked)

        self.messages = QPlainTextEdit()
        program_layout.addWidget(self.messages)

        figure = LaunchpadFigure()
        layout.addWidget(figure)

    @Slot()
    def on_program_clicked(self):
        # self.program_button.setDisabled(True)
        self.messages.clear()

        try:
            if is_resource(__name__, "lenlab_firmware.bin"):
                self.messages.insertPlainText(
                    "Lese die Firmware-Binärdatei aus dem Python-Paket\n"
                )
                firmware = read_binary("lenlab", "lenlab_firmware.bin")
            else:
                self.messages.insertPlainText(
                    "Lese die Firmware-Binärdatei aus dem Projektverzeichnis\n"
                )
                project_path = Path(__file__).resolve().parent.parent.parent
                firmware_file = (
                    project_path
                    / "workspace"
                    / "lenlab_firmware"
                    / "Debug"
                    / "lenlab_firmware.bin"
                )
                firmware = firmware_file.read_bytes()

            self.bsl.program(firmware)

        except OSError as error:
            self.messages.insertPlainText(
                f"Fehler beim Lesen der Firmware-Binärdatei: {str(error)}\n"
            )
            # self.program_button.setDisabled(False)

    @Slot(Message)
    def on_message(self, message: Message):
        self.messages.insertPlainText(f"{message}\n")

    @Slot(bool)
    def on_finished(self, success: bool):
        pass
        # self.program_button.setDisabled(False)
