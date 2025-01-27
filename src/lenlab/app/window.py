from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..controller.report import Report
from ..message import Message
from .poster import PosterWidget


class MainWindow(QMainWindow):
    def __init__(self, report: Report):
        super().__init__()

        self.report = report

        # widget
        layout = QVBoxLayout()

        self.status_poster = PosterWidget()
        self.status_poster.set_error(ExampleMessage())
        layout.addWidget(self.status_poster)

        self.tabs = []

        tab_widget = QTabWidget()
        for tab in self.tabs:
            tab_widget.addTab(tab, tab.title)

        layout.addWidget(tab_widget, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        # menu
        menu_bar = self.menuBar()

        menu = menu_bar.addMenu("&Lenlab")

        action = QAction("Save error report", self)
        action.triggered.connect(self.save_report)
        menu.addAction(action)

        menu.addSeparator()

        action = QAction("Quit", self)
        action.triggered.connect(self.close)
        menu.addAction(action)

        # title
        self.setWindowTitle("Lenlab")

    @Slot()
    def save_report(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self, "Save error report", self.report.file_name, self.report.file_format
        )
        if file_name:
            self.report.save_as(file_name)


class ExampleMessage(Message):
    english = """Example
    
    Message
    """
