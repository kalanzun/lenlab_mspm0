from PySide6.QtWidgets import QMainWindow, QTabWidget

from .bode import BodePlotter
from .oscilloscope import Oscilloscope
from .programmer import Programmer
from .voltmeter import Voltmeter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        tab_widget = QTabWidget()

        programmer = Programmer()
        tab_widget.addTab(programmer, programmer.title)

        voltmeter = Voltmeter()
        tab_widget.addTab(voltmeter, voltmeter.title)

        oscilloscope = Oscilloscope()
        tab_widget.addTab(oscilloscope, oscilloscope.title)

        bode = BodePlotter()
        tab_widget.addTab(bode, bode.title)

        self.setCentralWidget(tab_widget)

        self.setWindowTitle("Lenlab")
