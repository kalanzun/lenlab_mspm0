from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..model.lenlab import Lenlab
from .banner import MessageBanner
from .bode import BodePlotter
from .oscilloscope import Oscilloscope
from .programmer import ProgrammerWidget
from .voltmeter import Voltmeter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        message_banner = MessageBanner()
        # self.launchpad.ready.connect(message_banner.hide)
        # self.launchpad.error.connect(message_banner.set_message)
        # message_banner.retry_button.clicked.connect(self.launchpad.retry)

        self.lenlab = Lenlab()
        # self.lenlab.error.connect(message_banner.set_message)

        programmer = ProgrammerWidget()
        voltmeter = Voltmeter(self.lenlab)
        oscilloscope = Oscilloscope(self.lenlab)
        bode = BodePlotter(self.lenlab)

        tab_widget = QTabWidget()
        tab_widget.addTab(programmer, programmer.title)
        tab_widget.addTab(voltmeter, voltmeter.title)
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
