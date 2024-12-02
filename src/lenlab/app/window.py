import ctypes
import platform

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from ..model.lenlab import Lenlab
from .banner import MessageBanner
from .bode import BodePlotter
from .figure import PinAssignmentWidget
from .oscilloscope import Oscilloscope
from .programmer import ProgrammerWidget
from .vocabulary import Vocabulary as Vocab
from .voltmeter import VoltmeterWidget

# https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
ES_AWAYMODE_REQUIRED = 0x00000040
ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
ES_SYSTEM_REQUIRED = 0x00000001
ES_USER_PRESENT = 0x00000004


class MainWindow(QMainWindow):
    ready = Signal()

    def __init__(self):
        super().__init__()

        self.lenlab = Lenlab()

        message_banner = MessageBanner(button_text=Vocab.retry)
        self.lenlab.error.connect(message_banner.set_error)
        self.lenlab.new_terminal.connect(message_banner.hide)
        message_banner.button.clicked.connect(self.lenlab.retry)
        self.ready.connect(self.lenlab.retry, Qt.ConnectionType.QueuedConnection)

        programmer = ProgrammerWidget(self.lenlab)
        pins = PinAssignmentWidget()
        self.voltmeter_widget = VoltmeterWidget(self.lenlab)
        if platform.system() == "Windows":
            self.voltmeter_widget.voltmeter.active_changed.connect(self.inhibit_windows_sleep_mode)
        oscilloscope = Oscilloscope(self.lenlab)
        bode = BodePlotter(self.lenlab)

        tab_widget = QTabWidget()
        tab_widget.addTab(programmer, str(programmer.title))
        tab_widget.addTab(pins, str(pins.title))
        tab_widget.addTab(self.voltmeter_widget, str(self.voltmeter_widget.title))
        tab_widget.addTab(oscilloscope, str(oscilloscope.title))
        tab_widget.addTab(bode, str(bode.title))

        # self.lenlab.ready.connect(lambda: tab_widget.setCurrentIndex(1))

        layout = QVBoxLayout()
        layout.addWidget(message_banner)
        layout.addWidget(tab_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.setWindowTitle("Lenlab")
        self.ready.emit()

    def closeEvent(self, event):
        self.voltmeter_widget.closeEvent(event)

    @Slot(bool)
    def inhibit_windows_sleep_mode(self, inhibit: bool):
        # works only on Windows, do not connect on other systems
        # with ES_AWAYMODE_REQUIRED, the USB device vanished
        # ES_SYSTEM_REQUIRED inhibits sleep
        # ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED inhibits "display off"
        # "display off" seems fine, sleep closes the USB device
        state = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if inhibit else 0)
        ctypes.windll.kernel32.SetThreadExecutionState(state)
