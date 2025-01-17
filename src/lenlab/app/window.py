from attrs import frozen
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QPushButton, QTabWidget, QVBoxLayout, QWidget

from lenlab.app.status import BoardStatus
from lenlab.message import Message


@frozen
class Tab:
    widget: QWidget
    title: str


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.board_status = BoardStatus()

        tab_widget = QTabWidget()
        tab_widget.addTab(QWidget(), "Launchpad")
        tab_widget.addTab(QWidget(), "Programmer")
        tab_widget.addTab(QWidget(), "Voltmeter")
        tab_widget.addTab(QWidget(), "Oscilloscope")
        tab_widget.addTab(QWidget(), "Bode Plotter")

        self.i = 0
        button = QPushButton("Button")
        button.clicked.connect(self.on_button_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.board_status)
        layout.addWidget(button)
        layout.addWidget(tab_widget, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)
        self.setWindowTitle("Lenlab")

    @Slot()
    def on_button_clicked(self):
        if self.i:
            self.board_status.set_error(NoLaunchpad())
            self.i = 0
        else:
            self.board_status.set_ready()
            self.i = 1


class NoLaunchpad(Message):
    english = """
    No Launchpad found

    Please connect the Launchpad via USB to the computer."""

    german = """
    Kein Launchpad gefunden

    Bitte das Launchpad über USB mit dem Computer verbinden."""
