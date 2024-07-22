from importlib.resources import files

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
from .launchpad import Launchpad
from .message import Message


class Programmer(QWidget):
    title = "Programmer"
    description = "MSPM0 flash programming tool"

    def __init__(self, launchpad: Launchpad):
        super().__init__()

        self.bsl = BootstrapLoader(launchpad)
        self.bsl.launchpad.ready.connect(self.on_ready)
        self.bsl.launchpad.error.connect(self.on_error)
        self.bsl.message.connect(self.on_message)
        self.bsl.finished.connect(self.on_finished)

        figure = LaunchpadFigure()

        self.program_button = QPushButton("Program")
        self.program_button.setEnabled(False)
        self.program_button.clicked.connect(self.on_program_clicked)

        self.messages = QPlainTextEdit()

        program_layout = QVBoxLayout()
        program_layout.addWidget(self.program_button)
        program_layout.addWidget(self.messages)

        layout = QHBoxLayout()
        layout.addLayout(program_layout)
        layout.addWidget(figure)

        self.setLayout(layout)

    @Slot()
    def on_ready(self):
        self.program_button.setEnabled(True)

    @Slot(Message)
    def on_error(self, msg: Message):
        self.program_button.setEnabled(False)

    @Slot()
    def on_program_clicked(self):
        self.program_button.setDisabled(True)
        self.messages.clear()

        try:
            firmware_file = files() / ".." / "firmware" / "Debug" / "firmware.bin"
            firmware_file = firmware_file.resolve()
            firmware = firmware_file.read_bytes()

            self.bsl.program(firmware)

        except OSError as error:
            self.messages.insertPlainText(
                f"Fehler beim Lesen der Firmware-Binärdatei: {str(error)}"
            )
            self.program_button.setDisabled(False)

    @Slot(Message)
    def on_message(self, message: Message):
        self.messages.insertPlainText(str(message))
        self.messages.insertPlainText("\n")

    @Slot(bool)
    def on_finished(self, success: bool):
        self.program_button.setDisabled(False)
