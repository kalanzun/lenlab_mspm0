from PySide6.QtCore import Slot
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from .banner import MessageBanner
from .programmer import Programmer
from .terminal import Terminal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
        widget.setLayout(layout)

        self.banner = MessageBanner()
        layout.addWidget(self.banner)
        self.banner.button.clicked.connect(self.on_banner_button_clicked)

        self.terminal = Terminal()
        self.terminal.ready.connect(self.banner.hide)
        self.terminal.error.connect(
            lambda message: self.banner.set_error(message, "Retry")
        )

        programmer = Programmer(self.terminal)

        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        tab_widget.addTab(programmer, programmer.title)
        # tab_widget.addTab(voltmeter, voltmeter.title)
        # tab_widget.addTab(oscilloscope, oscilloscope.title)
        # tab_widget.addTab(bode, bode.title)

        self.setWindowTitle("Lenlab")
        self.terminal.open(QSerialPortInfo.availablePorts())

    @Slot()
    def on_banner_button_clicked(self):
        self.terminal.close()
        self.terminal.open(QSerialPortInfo.availablePorts())
