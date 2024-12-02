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

from ..launchpad.bsl import Programmer
from ..message import Message
from ..model.lenlab import Lenlab
from .banner import MessageBanner
from .figure import LaunchpadFigure, PainterWidget
from .vocabulary import Vocabulary as Vocab


class ProgrammerWidget(QWidget):
    title = Vocab("Programmer", "Programmierer")

    programmer: Programmer

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        introduction = QLabel(self)
        introduction.setTextFormat(Qt.TextFormat.MarkdownText)
        introduction.setWordWrap(True)
        introduction.setText(str(Introduction()))

        self.program_button = QPushButton(str(Vocab.program))
        self.program_button.clicked.connect(self.on_program_clicked)
        self.progress_bar = QProgressBar()
        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)
        self.banner = MessageBanner()

        figure = PainterWidget(LaunchpadFigure)

        program_layout = QVBoxLayout()
        program_layout.addWidget(introduction)
        program_layout.addWidget(self.program_button)
        program_layout.addWidget(self.progress_bar)
        program_layout.addWidget(self.messages)
        program_layout.addWidget(self.banner)

        button = QPushButton(str(Vocab("Export Firmware", "Firmware Exportieren")))
        button.clicked.connect(self.on_export_clicked)
        program_layout.addWidget(button)

        layout = QHBoxLayout()
        layout.addLayout(program_layout)
        layout.addWidget(figure)

        self.setLayout(layout)

    @Slot()
    def on_program_clicked(self):
        self.program_button.setEnabled(False)
        self.messages.clear()
        self.banner.hide()

        self.lenlab.remove_terminal()

        self.programmer = Programmer()
        self.programmer.message.connect(self.on_message)
        self.programmer.success.connect(self.on_success)
        self.programmer.error.connect(self.on_error)

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.programmer.n_messages)

        self.programmer.program()

    @Slot(Message)
    def on_message(self, message: Message):
        self.progress_bar.setValue(self.progress_bar.value() + message.progress)
        self.messages.appendPlainText(str(message))

    @Slot()
    def on_success(self):
        self.program_button.setEnabled(True)
        self.banner.set_success(Successful())

        self.lenlab.retry()

    @Slot(Message)
    def on_error(self, error: Message):
        self.program_button.setEnabled(True)
        self.banner.set_error(error)

        self.lenlab.retry()

    @Slot()
    def on_export_clicked(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self,
            str(Vocab("Export Firmware", "Firmware Exportieren")),
            "lenlab_fw.bin",
            "Binary (*.bin)",
        )
        if not file_name:  # cancelled
            return

        try:
            firmware = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()
            Path(file_name).write_bytes(firmware)
        except Exception as error:
            self.banner.set_error(ExportError(error))


class Introduction(Message):
    english = """### Please start the "Bootstrap Loader" on the Launchpad first:
    
    Press and hold the button S1 next to the green LED and press the button Reset
    next to the USB plug. Let the button S1 go shortly after (min. 100 ms).
    
    The buttons click audibly. The red LED at the lower edge is off.
    You have now 10 seconds to click on Program here in the app."""

    german = """### Bitte starten Sie zuerst den "Bootstrap Loader" auf dem Launchpad:
    
    Halten Sie die Taste S1 neben der grünen LED gedrückt und drücken Sie auf die Taste Reset
    neben dem USB-Stecker. Lassen Sie die Taste S1 kurz danach wieder los (min. 100 ms).
    
    Die Tasten klicken hörbar. Die rote LED an der Unterkante ist aus.
    Sie haben jetzt 10 Sekunden, um hier in der App auf Programmieren zu klicken."""


class Successful(Message):
    english = """### Programming successful
    
    The programmer wrote the Lenlab firmware to the Launchpad.
    Lenlab should be connected and ready for measurements."""

    german = """### Programmieren erfolgreich
    
    Der Programmierer schrieb die Lenlab Firmware auf das Launchpad.
    Lenlab sollte verbunden sein und bereit für Messungen."""


class ExportError(Message):
    english = """Error exporting the firmware:\n\n{0}"""
    german = """Fehler beim Exportieren der Firmware:\n\n{0}"""
