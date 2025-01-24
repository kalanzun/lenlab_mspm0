from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from lenlab.app.poster import StatusPoster

from ..device.lenlab import Lenlab
from .bode import BodePlotter
from .launchpad import LaunchpadWidget
from .oscilloscope import OscilloscopeWidget
from .programmer import ProgrammerWidget
from .voltmeter import VoltmeterWidget


class MainWindow(QMainWindow):
    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        # widget
        self.status_poster = StatusPoster()
        self.status_poster.attach(self.lenlab.discovery)

        self.tabs = [
            LaunchpadWidget(self.lenlab),
            ProgrammerWidget(self.lenlab),
            VoltmeterWidget(self.lenlab),
            OscilloscopeWidget(self.lenlab),
            BodePlotter(self.lenlab),
        ]

        tab_widget = QTabWidget()
        for tab in self.tabs:
            tab_widget.addTab(tab, tab.title)

        layout = QVBoxLayout()
        layout.addWidget(self.status_poster)
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
            file.write(self.lenlab.error_report.getvalue())
