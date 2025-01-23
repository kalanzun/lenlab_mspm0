from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from lenlab.app.status import FirmwareStatus
from lenlab.device.device import Device
from lenlab.device.lenlab import Lenlab


class LaunchpadWidget(QWidget):
    title = "Launchpad"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.device = Device(lenlab)

        self.chart = QWidget()
        self.status = FirmwareStatus(self.device)

        tool_box = QVBoxLayout()
        tool_box.addWidget(self.status)
        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.chart, 1)
        layout.addLayout(tool_box)

        self.setLayout(layout)
