from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from .banner import MessageBanner
from .bode import BodePlotter
from .manager import PortManager
from .oscilloscope import Oscilloscope
from .programmer import Programmer
from .voltmeter import Voltmeter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        message_banner = MessageBanner()

        self.port_manager = PortManager()
        # self.port_manager.ready.connect(message_banner.hide)
        self.port_manager.message.connect(message_banner.set_message)
        message_banner.retry_button.clicked.connect(self.port_manager.retry)
        self.port_manager.open_launchpad()

        programmer = Programmer(self.port_manager)
        voltmeter = Voltmeter()
        oscilloscope = Oscilloscope()
        bode = BodePlotter()

        tab_widget = QTabWidget()
        tab_widget.addTab(programmer, programmer.title)
        tab_widget.addTab(voltmeter, voltmeter.title)
        tab_widget.addTab(oscilloscope, oscilloscope.title)
        tab_widget.addTab(bode, bode.title)

        layout = QVBoxLayout()
        layout.addWidget(message_banner)
        layout.addWidget(tab_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setWindowTitle("Lenlab")
