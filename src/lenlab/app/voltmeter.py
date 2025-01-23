from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from lenlab.app.status import FirmwareStatus
from lenlab.device.lenlab import Lenlab
from lenlab.device.voltmeter import Voltmeter


class VoltmeterWidget(QWidget):
    title = "Voltmeter"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.voltmeter = Voltmeter(lenlab)

        self.chart = QWidget()
        self.status = FirmwareStatus(self.voltmeter)

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
