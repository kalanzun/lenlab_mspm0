from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QSlider

from .lenlab import Lenlab


class SignalGenerator(QWidget):

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        layout = QVBoxLayout()
        main_layout.addLayout(layout)

        label = QLabel("Amplitude")
        layout.addWidget(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(slider)

        slider.setMinimum(-1650)
        slider.setMaximum(1650)
        slider.valueChanged.connect(self.on_amplitude_value_changed)

    @Slot()
    def on_amplitude_value_changed(self, value: int):
        self.lenlab.command(b"C", value)
