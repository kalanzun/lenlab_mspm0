from importlib import resources
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import lenlab

from ..controller.programmer import Programmer
from ..launchpad.discovery import Discovery
from ..message import Message
from .figure import LaunchpadFigure
from .poster import PosterWidget


class ProgrammerWidget(QWidget):
    title = "Programmer"

    def __init__(self, discovery: Discovery):
        super().__init__()
        self.programmer = Programmer(discovery)
        self.programmer.message.connect(self.on_message)
        self.programmer.success.connect(self.on_success)
        self.programmer.error.connect(self.on_error)

        program_layout = QVBoxLayout()

        introduction = QLabel(self)
        introduction.setTextFormat(Qt.TextFormat.MarkdownText)
        introduction.setWordWrap(True)
        introduction.setText("### " + Introduction().long_form())
        program_layout.addWidget(introduction)

        self.program_button = QPushButton("Program")
        self.program_button.clicked.connect(self.on_program_clicked)
        program_layout.addWidget(self.program_button)

        self.progress_bar = QProgressBar()
        program_layout.addWidget(self.progress_bar)

        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)
        program_layout.addWidget(self.messages)

        self.poster = PosterWidget()
        self.poster.setHidden(True)
        program_layout.addWidget(self.poster)

        button = QPushButton("Export Firmware")
        button.clicked.connect(self.on_export_clicked)
        program_layout.addWidget(button)

        tool_box = QVBoxLayout()

        figure = LaunchpadFigure()
        tool_box.addWidget(figure)

        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addLayout(program_layout)
        layout.addLayout(tool_box)

        self.setLayout(layout)

    @Slot()
    def on_program_clicked(self):
        self.program_button.setEnabled(False)
        self.messages.clear()
        self.poster.hide()

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.programmer.n_messages)

        self.programmer.start()

    @Slot(Message)
    def on_message(self, message):
        self.progress_bar.setValue(self.progress_bar.value() + message.progress)
        self.messages.appendPlainText(str(message))

    @Slot(Message)
    def on_success(self, message):
        self.program_button.setEnabled(True)
        self.poster.set_success(message)

    @Slot(Message)
    def on_error(self, error):
        self.program_button.setEnabled(True)
        self.poster.set_error(error)

    @Slot()
    def on_export_clicked(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self,
            "Export Firmware",
            "lenlab_fw.bin",
            "Binary (*.bin)",
        )
        if not file_name:  # cancelled
            return

        try:
            firmware = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()
            Path(file_name).write_bytes(firmware)
        except Exception as error:
            self.poster.set_error(ExportError(error))


class Introduction(Message):
    english = """Please start the "Bootstrap Loader" on the Launchpad first:

    Press and hold the button S1 next to the green LED and press the button Reset
    next to the USB plug. Let the button S1 go shortly after (min. 100 ms).

    The buttons click audibly. The red LED at the lower edge is off.
    You have now 10 seconds to click on Program here in the app."""

    german = """Bitte starten Sie zuerst den "Bootstrap Loader" auf dem Launchpad:

    Halten Sie die Taste S1 neben der grünen LED gedrückt und drücken Sie auf die Taste Reset
    neben dem USB-Stecker. Lassen Sie die Taste S1 kurz danach wieder los (min. 100 ms).

    Die Tasten klicken hörbar. Die rote LED an der Unterkante ist aus.
    Sie haben jetzt 10 Sekunden, um hier in der App auf Programmieren zu klicken."""


class ExportError(Message):
    english = """Error exporting the firmware\n\n{0}"""
    german = """Fehler beim Exportieren der Firmware\n\n{0}"""
