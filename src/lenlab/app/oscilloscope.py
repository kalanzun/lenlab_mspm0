from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from lenlab.app.status import FirmwareStatus
from lenlab.device.lenlab import Lenlab
from lenlab.device.oscilloscope import Oscilloscope


class OscilloscopeWidget(QWidget):
    title = "Oscilloscope"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.oscilloscope = Oscilloscope(lenlab)

        self.chart = QWidget()
        self.status = FirmwareStatus(self.oscilloscope)

        start = QPushButton("Start")
        stop = QPushButton("Stop")

        button_box = QHBoxLayout()
        button_box.addWidget(start)
        button_box.addWidget(stop)

        tool_box = QVBoxLayout()
        tool_box.addWidget(self.status)
        tool_box.addLayout(button_box)
        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.chart, 1)
        layout.addLayout(tool_box)

        self.setLayout(layout)
