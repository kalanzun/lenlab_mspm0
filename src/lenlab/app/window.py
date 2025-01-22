from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..launchpad.discovery import Discovery
from .status import BoardStatus


class MainWindow(QMainWindow):
    def __init__(self, discovery: Discovery):
        super().__init__()

        self.discovery = discovery

        self.board_status = BoardStatus(self.discovery)

        tab_widget = QTabWidget()
        tab_widget.addTab(QWidget(), "Launchpad")
        tab_widget.addTab(QWidget(), "Programmer")
        tab_widget.addTab(QWidget(), "Voltmeter")
        tab_widget.addTab(QWidget(), "Oscilloscope")
        tab_widget.addTab(QWidget(), "Bode Plotter")

        layout = QVBoxLayout()
        layout.addWidget(self.board_status)
        layout.addWidget(tab_widget, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)
        self.setWindowTitle("Lenlab")
