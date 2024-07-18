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
from .manager import PortManager


class Programmer(QWidget):
    title = "Programmer"
    description = "MSPM0 flash programming tool"

    def __init__(self, port_manager: PortManager):
        super().__init__()

        self.port_manager = port_manager
        self.bsl = None

        figure = LaunchpadFigure()

        self.program_button = QPushButton("Program")
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
    def on_program_clicked(self):
        self.program_button.setDisabled(True)
        if self.bsl is not None:
            return

        self.messages.clear()

        try:
            path = files() / "firmware.out"
            firmware = path.read_bytes()
        except OSError as error:
            self.messages.insertPlainText(
                f"Fehler beim Lesen der Firmware-Binärdatei: {str(error)}"
            )
            self.program_button.setDisabled(False)
            return

        self.bsl = BootstrapLoader(self.port_manager.port, firmware)
        self.bsl.message.connect(self.on_message)
        self.bsl.finished.connect(self.on_finished)
        self.bsl.start()

    @Slot(str)
    def on_message(self, message):
        self.messages.insertPlainText(message)
        self.messages.insertPlainText("\n")

    @Slot(bool)
    def on_finished(self, success):
        self.bsl = None
        self.program_button.setDisabled(False)
