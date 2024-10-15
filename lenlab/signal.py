from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QSlider, QPushButton, QHBoxLayout, QLineEdit

from .lenlab import Lenlab


class SignalGenerator(QWidget):

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.toggle_button = QPushButton("Signal generator")
        button_layout.addWidget(self.toggle_button)
        button_layout.addStretch(1)

        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.on_toggled)

        self.signal_widget = SignalWidget(lenlab)
        main_layout.addWidget(self.signal_widget)

        self.signal_widget.setHidden(True)

    def on_toggled(self, checked: bool):
        if checked:
            self.signal_widget.show()
        else:
            self.signal_widget.hide()


class SignalWidget(QWidget):

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        layout = QVBoxLayout()
        main_layout.addLayout(layout)

        line = QHBoxLayout()
        layout.addLayout(line)

        label = QLabel("Amplitude [V]")
        line.addWidget(label)

        self.edit = QLineEdit("0.000")
        line.addWidget(self.edit)
        line.addStretch(1)
        self.edit.editingFinished.connect(self.on_editing_finished)

        ticks = QHBoxLayout()
        layout.addLayout(ticks)

        label = QLabel("0V")
        ticks.addWidget(label)
        ticks.addStretch(1)

        label = QLabel("1.1V")
        ticks.addWidget(label)
        ticks.addStretch(1)

        label = QLabel("2.2V")
        ticks.addWidget(label)
        ticks.addStretch(1)

        label = QLabel("3.3V")
        ticks.addWidget(label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.slider)

        self.slider.setMinimum(-1650)
        self.slider.setValue(-1650)
        self.slider.setMaximum(1650)
        self.slider.setTickInterval(550)
        self.slider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.slider.valueChanged.connect(self.on_slider_value_changed)

    @Slot()
    def on_slider_value_changed(self, value: int):
        # payload = b"c" + value.to_bytes(4, byteorder="little", signed=True)
        # self.lenlab.command(payload)
        self.lenlab.set_signal_constant(value)
        value = (value + 1650) / 1000
        self.edit.setText(f"{value:.3f}")

    @Slot()
    def on_editing_finished(self):
        text = self.edit.text()
        text = text.replace(",", ".")
        try:
            value = int(round(float(text) * 1000)) - 1650
            value = min(value, 1650)
            value = max(value, -1650)
            self.slider.setValue(value)
        except ValueError:
            self.slider.valueChanged.emit(self.slider.value())
