from importlib import resources
from pathlib import Path

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import lenlab

from ..controller.programmer import Programmer
from ..launchpad.discovery import Discovery
from ..message import Message
from ..translate import Translate, tr
from .figure import LaunchpadFigure
from .poster import PosterWidget
from .save_as import SaveAs


class ProgrammerWidget(QWidget):
    title = Translate("Programmer", "Programmierer")

    about = Signal()

    def __init__(self, discovery: Discovery):
        super().__init__()
        self.programmer = Programmer(discovery)
        self.programmer.message.connect(self.on_message)
        self.programmer.success.connect(self.on_success)
        self.programmer.error.connect(self.on_error)

        program_layout = QVBoxLayout()

        introduction = QTextBrowser(self)
        introduction.setFrameShape(QFrame.Shape.NoFrame)
        introduction.setMarkdown("### " + Introduction().long_form())
        introduction.setOpenLinks(False)
        introduction.anchorClicked.connect(self.on_link_activated)
        program_layout.addWidget(introduction)

        self.program_button = QPushButton(tr("Program", "Programmieren"))
        self.program_button.clicked.connect(self.on_program_clicked)
        program_layout.addWidget(self.program_button)

        self.progress_bar = QProgressBar()
        program_layout.addWidget(self.progress_bar)

        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)
        program_layout.addWidget(self.messages)

        self.poster = PosterWidget()
        self.poster.setHidden(True)
        self.poster.text_widget.linkActivated.connect(self.on_link_activated)
        program_layout.addWidget(self.poster)

        button = QPushButton(tr("Export Firmware", "Firmware exportieren"))
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
        dialog = SaveAs(self)
        dialog.setWindowTitle(tr("Export firmware", "Firmware exportieren"))
        dialog.set_default_file_name("lenlab_fw.bin")
        dialog.on_save_as = self.on_export
        dialog.open()

    @staticmethod
    def on_export(file_path: Path):
        firmware = (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()
        file_path.write_bytes(firmware)

    @Slot(str)
    def on_link_activated(self, link: str):
        self.about.emit()


class Introduction(Message):
    english = """Programmer for the red Launchpad LP-MSPM0G3507.
    
    Please use TI UniFlash ([Instructions](about)) for the black MSP-LITO-G3507 instead.
    
    ### Please start the "Bootstrap Loader" on the Launchpad first:

    Press and hold the button S1 next to the green LED and press the button Reset
    next to the USB plug. Let the button S1 go shortly after (min. 100 ms).

    The buttons click audibly. The red LED at the lower edge is off.
    You have now 10 seconds to click on Program here in the app.
    """
    german = """Programmierer für das rote Launchpad LP-MSPM0G3507.
    
    Bitte verwenden Sie TI UniFlash ([Anleitung](about)) für das schwarze MSP-LITO-G3507.
    
    ### Bitte starten Sie zuerst den "Bootstrap Loader" auf dem Launchpad:

    Halten Sie die Taste S1 neben der grünen LED gedrückt und drücken Sie auf die Taste Reset
    neben dem USB-Stecker. Lassen Sie die Taste S1 kurz danach wieder los (min. 100 ms).

    Die Tasten klicken hörbar. Die rote LED an der Unterkante ist aus.
    Sie haben jetzt 10 Sekunden, um hier in der App auf Programmieren zu klicken.
    """
