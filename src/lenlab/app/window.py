from PySide6.QtWidgets import QMainWindow

from ..controller.discovery import Discovery
from .box import Box


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.box = Box()
        self.setCentralWidget(self.box)

        self.discovery = Discovery()
        self.discovery.error.connect(self.box.set_error)
        self.discovery.discover_later.emit()

        self.setWindowTitle("Lenlab")
