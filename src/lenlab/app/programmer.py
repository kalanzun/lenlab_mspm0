from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .figure import LaunchpadFigure


class Programmer(QWidget):
    title = "Programmer"
    description = "MSPM0 flash programming tool"

    def __init__(self):
        super().__init__()

        self.program_button = QPushButton("Program")
        self.program_button.setEnabled(False)
        self.program_button.clicked.connect(self.on_program_clicked)

        self.messages = QPlainTextEdit()

        figure = LaunchpadFigure()

        program_layout = QVBoxLayout()
        program_layout.addWidget(self.program_button)
        program_layout.addWidget(self.messages)

        layout = QHBoxLayout()
        layout.addLayout(program_layout)
        layout.addWidget(figure)

        self.setLayout(layout)

    @Slot()
    def on_program_clicked(self):
        pass
