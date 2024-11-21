from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..model.lenlab import Lenlab
from .banner import MessageBanner
from .bode import BodePlotter
from .figure import PinAssignmentWidget
from .oscilloscope import Oscilloscope
from .programmer import ProgrammerWidget
from .voltmeter import VoltmeterWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.lenlab = Lenlab()

        message_banner = MessageBanner()
        self.lenlab.error.connect(message_banner.set_error)
        self.lenlab.new_terminal.connect(message_banner.hide)
        message_banner.retry_button.clicked.connect(self.lenlab.retry)

        programmer = ProgrammerWidget(self.lenlab)
        pins = PinAssignmentWidget()
        self.voltmeter_widget = VoltmeterWidget(self.lenlab)
        oscilloscope = Oscilloscope(self.lenlab)
        bode = BodePlotter(self.lenlab)

        tab_widget = QTabWidget()
        tab_widget.addTab(programmer, programmer.title)
        tab_widget.addTab(pins, pins.title)
        tab_widget.addTab(self.voltmeter_widget, self.voltmeter_widget.title)
        tab_widget.addTab(oscilloscope, oscilloscope.title)
        tab_widget.addTab(bode, bode.title)

        # self.lenlab.ready.connect(lambda: tab_widget.setCurrentIndex(1))

        layout = QVBoxLayout()
        layout.addWidget(message_banner)
        layout.addWidget(tab_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setWindowTitle("Lenlab")
        self.lenlab.retry()

    def closeEvent(self, event):
        self.voltmeter_widget.closeEvent(event)
