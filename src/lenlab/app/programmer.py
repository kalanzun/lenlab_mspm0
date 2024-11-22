from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..launchpad.bsl import Programmer
from ..message import Message
from ..model.lenlab import Lenlab
from .banner import MessageBanner
from .figure import LaunchpadFigure


class ProgrammerWidget(QWidget):
    title = "Programmer"

    programmer: Programmer

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        introduction = QLabel(self)
        introduction.setText(str(Introduction()))

        self.program_button = QPushButton("Program")
        self.program_button.clicked.connect(self.on_program_clicked)
        self.progress_bar = QProgressBar()
        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)
        self.banner = MessageBanner(button=False)

        figure = LaunchpadFigure()

        program_layout = QVBoxLayout()
        program_layout.addWidget(introduction)
        program_layout.addWidget(self.program_button)
        program_layout.addWidget(self.progress_bar)
        program_layout.addWidget(self.messages)
        program_layout.addWidget(self.banner)

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


class Introduction(Message):
    english = """
    Please start the "Bootstrap Loader" on the Launchpad first:
    Press and hold the button S1 next to the green LED and press the button Reset
    next to the USB plug. Let the button S1 go shortly after (min. 100 ms).
    The buttons click audibly. The red LED at the lower edge stops blinking and stays off.
    You have now 10 seconds to click on Program here in the app.
    """

    german = """
    Bitte starten Sie zuerst den "Bootstrap Loader" auf dem Launchpad:
    Halten Sie die Taste S1 neben der grünen LED gedrückt und drücken Sie auf die Taste Reset
    neben dem USB-Stecker. Lassen Sie die Taste S1 kurz danach wieder los (min. 100 ms).
    Die Tasten klicken hörbar. Die rote LED an der Unterkante hört auf zu blinken und bleibt aus.
    Sie haben jetzt 10 Sekunden, um hier in der App auf Programmieren zu klicken.
    """


class Start(Message):
    english = "Start"
    german = "Start"


class Programming(Message):
    english = "Programming"
    german = "Programmieren"


class Successful(Message):
    english = "Successful"
    german = "Erfolgreich"
