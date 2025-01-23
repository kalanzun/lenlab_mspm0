from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from lenlab.app.status import LaunchpadStatus
from lenlab.device.lenlab import Lenlab
from lenlab.device.programmer import Programmer


class ProgrammerWidget(QWidget):
    title = "Programmer"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.programmer = Programmer(lenlab)

        self.chart = QWidget()
        self.status = LaunchpadStatus(self.programmer)

        tool_box = QVBoxLayout()
        tool_box.addWidget(self.status)
        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.chart, 1)
        layout.addLayout(tool_box)

        self.setLayout(layout)
