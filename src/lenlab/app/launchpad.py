from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from lenlab.app.poster import FirmwareStatus
from lenlab.device.device import Device
from lenlab.device.lenlab import Lenlab


class LaunchpadWidget(QWidget):
    title = "Launchpad"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.device = Device(lenlab)

        self.chart = QWidget()
        status = FirmwareStatus()
        status.attach(lenlab.discovery)

        tool_box = QVBoxLayout()
        tool_box.addWidget(status)
        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.chart, 1)
        layout.addLayout(tool_box)

        self.setLayout(layout)
