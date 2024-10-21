from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

from .banner import MessageBanner


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.i = 0

        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.banner = MessageBanner()
        layout.addWidget(self.banner)

        button = QPushButton("New Message")
        layout.addWidget(button)
        button.clicked.connect(self.new_message)
        button.clicked.emit()

        layout.addStretch(1)

        self.setWindowTitle("Lenlab")

    @Slot()
    def new_message(self):
        if self.i == 0:
            self.banner.set_info("Welcome to Lenlab 8!")
            self.i = 1
        elif self.i == 1:
            self.banner.set_warning(
                "No Launchpad found\nPlease connect a Launchpad.", "Retry"
            )
            self.i = 2
        elif self.i == 2:
            self.banner.set_error(
                "Unknown firmware\nPlease program the Lenlab firmware.", "Retry"
            )
            self.i = 3
        else:
            self.banner.hide()
            self.i = 0
