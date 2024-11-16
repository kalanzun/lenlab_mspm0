from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..launchpad.bsl import Programmer
from ..message import Message
from .banner import MessageBanner
from .figure import LaunchpadFigure


class ProgrammerWidget(QWidget):
    title = "Programmer"

    def __init__(self):
        super().__init__()

        self.programmer = None

        introduction = QLabel(self)
        introduction.setText(str(Introduction()))

        self.program_button = QPushButton("Program")
        self.program_button.clicked.connect(self.on_program_clicked)

        self.result = MessageBanner(button=False)
        self.result.set_warning(Start())

        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)

        figure = LaunchpadFigure()

        program_layout = QVBoxLayout()
        program_layout.addWidget(introduction)
        program_layout.addWidget(self.program_button)
        program_layout.addWidget(self.result)
        program_layout.addWidget(self.messages)

        layout = QHBoxLayout()
        layout.addLayout(program_layout)
        layout.addWidget(figure)

        self.setLayout(layout)

    @Slot()
    def on_program_clicked(self):
        self.program_button.setEnabled(False)
        self.messages.clear()
        self.result.set_warning(Programming())

        self.programmer = Programmer()
        self.programmer.message.connect(self.on_message)
        self.programmer.success.connect(self.on_success)
        self.programmer.error.connect(self.on_error)

        self.programmer.program()

    @Slot(Message)
    def on_message(self, message: Message):
        self.messages.appendPlainText(str(message))

    @Slot()
    def on_success(self):
        self.program_button.setEnabled(True)
        self.result.set_info(Successful())

    @Slot(Message)
    def on_error(self, error: Message):
        self.program_button.setEnabled(True)
        self.result.set_error(error)


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
