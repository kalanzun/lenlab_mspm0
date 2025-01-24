from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lenlab.app.poster import LaunchpadStatus, PosterWidget
from lenlab.device.lenlab import Lenlab
from lenlab.device.programmer import Programmer
from lenlab.message import Message


class ProgrammerWidget(QWidget):
    title = "Programmer"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.programmer = Programmer(lenlab)
        self.programmer.message.connect(self.on_message)
        self.programmer.success.connect(self.on_success)
        self.programmer.error.connect(self.on_error)

        program_layout = QVBoxLayout()

        status = LaunchpadStatus()
        status.attach(lenlab.discovery)
        program_layout.addWidget(status)

        introduction = QLabel(self)
        introduction.setTextFormat(Qt.TextFormat.MarkdownText)
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
        program_layout.addWidget(self.poster)

        # button = QPushButton("Export Firmware")
        # button.clicked.connect(self.on_export_clicked)
        # program_layout.addWidget(button)

        tool_box = QVBoxLayout()

        # figure = LaunchpadFigure()
        # tool_box.addWidget(figure)

        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addLayout(program_layout)
        layout.addLayout(tool_box)

        self.setLayout(layout)

    @Slot()
    def on_program_clicked(self):
        self.program_button.setEnabled(False)
        self.messages.clear()
        # self.banner.hide()

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.programmer.n_messages)

        self.programmer.start()

    @Slot(Message)
    def on_message(self, message):
        self.progress_bar.setValue(self.progress_bar.value() + message.progress)
        self.messages.appendPlainText(str(message))

    @Slot()
    def on_success(self):
        self.program_button.setEnabled(True)
        self.poster.set_success(Successful())

    @Slot(Message)
    def on_error(self, error: Message):
        self.program_button.setEnabled(True)
        self.poster.set_error(error)


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


class Successful(Message):
    english = """Programming successful

    The programmer wrote the Lenlab firmware to the Launchpad.
    Lenlab should be connected and ready for measurements."""

    german = """Programmieren erfolgreich

    Der Programmierer schrieb die Lenlab Firmware auf das Launchpad.
    Lenlab sollte verbunden sein und bereit für Messungen."""
