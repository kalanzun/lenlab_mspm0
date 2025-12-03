from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..controller.lenlab import Lenlab
from ..controller.report import Report
from ..translate import tr
from .about import About
from .bode import BodeWidget
from .figure import LaunchpadWidget, LitoWidget
from .oscilloscope import OscilloscopeWidget
from .poster import PosterWidget
from .programmer import ProgrammerWidget
from .save_as import SaveAs
from .voltmeter import VoltmeterWidget


class MainWindow(QMainWindow):
    def __init__(self, lenlab: Lenlab, report: Report, rules: bool = False):
        super().__init__()
        self.lenlab = lenlab
        self.report = report

        self.lenlab.close.connect(self.close)

        # widget
        layout = QVBoxLayout()

        self.status_poster = PosterWidget()
        self.status_poster.button.setHidden(False)
        self.status_poster.button.clicked.connect(self.lenlab.discovery.retry)
        self.status_poster.setHidden(True)
        self.lenlab.error.connect(self.status_poster.set_error)
        self.lenlab.ready.connect(self.status_poster.setHidden)
        layout.addWidget(self.status_poster)

        self.tabs = [
            LaunchpadWidget(),
            LitoWidget(),
            prog := ProgrammerWidget(lenlab.discovery),
            volt := VoltmeterWidget(lenlab),
            osci := OscilloscopeWidget(lenlab),
            bode := BodeWidget(lenlab),
            about := About(),
        ]

        self.voltmeter = volt

        osci.bode.connect(bode.bode.on_bode)

        tab_widget = QTabWidget()
        # tab_widget.setDocumentMode(True)  # no frame around pages
        for tab in self.tabs:
            tab_widget.addTab(tab, str(tab.title))

        prog.about.connect(lambda: tab_widget.setCurrentWidget(about))

        layout.addWidget(tab_widget, 1)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

        # menu
        menu_bar = self.menuBar()

        menu = menu_bar.addMenu("&Lenlab")

        self.report_action = QAction(tr("Save error report", "Fehlerbericht speichern"), self)
        self.report_action.triggered.connect(self.save_report_triggered)
        menu.addAction(self.report_action)

        if rules:
            self.rules_action = QAction(tr("Install rules", "Regeln installieren"), self)
            self.rules_action.triggered.connect(self.install_rules)
            menu.addAction(self.rules_action)

        menu.addSeparator()

        action = QAction(tr("Close", "Beenden"), self)
        action.triggered.connect(self.close)
        menu.addAction(action)

        # title
        self.setWindowTitle("Lenlab")

    @Slot()
    def save_report_triggered(self):
        dialog = SaveAs(self)
        dialog.setWindowTitle(tr("Save error report", "Fehlerbericht speichern"))
        dialog.set_default_file_name(self.report.file_name)
        dialog.on_save_as = self.save_report
        dialog.open()

    def save_report(self, file_path: Path):
        with file_path.open("w", encoding="utf-8", newline="\n") as file:
            self.report.save_as(file)

    @Slot()
    def install_rules(self):
        from ..launchpad import rules

        rules.install_rules()

    def closeEvent(self, event: QCloseEvent):
        self.voltmeter.on_close_event(event)
