from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from lenlab.app.poster import FirmwareStatus
from lenlab.device.bode import Bode
from lenlab.device.lenlab import Lenlab


class BodePlotter(QWidget):
    title = "Bode Plotter"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.bode = Bode(lenlab)

        self.chart = QWidget()
        status = FirmwareStatus()
        status.attach(lenlab.discovery)

        start = QPushButton("Start")
        cancel = QPushButton("Cancel")

        button_box = QHBoxLayout()
        button_box.addWidget(start)
        button_box.addWidget(cancel)

        tool_box = QVBoxLayout()
        tool_box.addWidget(status)
        tool_box.addLayout(button_box)
        tool_box.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.chart, 1)
        layout.addLayout(tool_box)

        self.setLayout(layout)
