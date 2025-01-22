import io

from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..launchpad.discovery import Discovery
from .bode import BodePlotter
from .launchpad import LaunchpadWidget
from .oscilloscope import OscilloscopeWidget
from .programmer import ProgrammerWidget
from .status import BoardStatus
from .voltmeter import VoltmeterWidget


class MainWindow(QMainWindow):
    def __init__(self, error_report: io.StringIO, discovery: Discovery):
        super().__init__()

        self.error_report = error_report
        self.discovery = discovery

        # widget
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

        # menu
        error_report = QAction("Save error report", self)
        error_report.triggered.connect(self.save_error_report)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)

        menu_bar = self.menuBar()

        menu = menu_bar.addMenu("&Lenlab")
        menu.addAction(error_report)
        menu.addSeparator()
        menu.addAction(quit_action)

        # title
        self.setWindowTitle("Lenlab")

    @Slot()
    def save_error_report(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self, "Save error report", "lenlab8-error-report.txt", "TXT (*.txt)"
        )
        if not file_name:  # cancelled
            return

        with open(file_name, "w", encoding="utf-8") as file:
            file.write(self.error_report.getvalue())
