from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QSlider, QWidget

from ..controller.lenlab import Lenlab
from ..controller.signal import sine_table
from ..launchpad.protocol import command


class Parameter(QObject):
    changed = Signal()

    def __init__(self, label: str):
        super().__init__()

        self.label = QLabel(label)

    def widgets(self):
        yield self.label


class Function(Parameter):
    def __init__(self):
        super().__init__("Signal generator")

        self.field = QLineEdit()
        self.field.setReadOnly(True)
        self.field.setText("Sinus")

    def widgets(self):
        yield from super().widgets()
        yield self.field


class Slider(Parameter):
    def __init__(self, label: str):
        super().__init__(label)

        self.field = QLineEdit()
        self.field.setText(self.format_value(0))
        self.field.setReadOnly(True)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.on_slider_value_changed)

    def widgets(self):
        yield from super().widgets()
        yield self.field
        yield self.slider

    @Slot(bool)
    def set_disabled(self, disabled):
        self.slider.setDisabled(disabled)
        if disabled:
            self.slider.setValue(0)

    def get_value(self):
        return self.slider.value()

    @staticmethod
    def format_value(value: int) -> str:
        return str(value)

    @Slot(int)
    def on_slider_value_changed(self, value):
        self.field.setText(self.format_value(value))
        self.changed.emit()


class Amplitude(Slider):
    def __init__(self, label: str = "Amplitude"):
        super().__init__(label)

        self.slider.setMaximum(255)

    def get_value(self):
        # 0 ... 2040
        return self.slider.value() * 8

    @staticmethod
    def format_value(value: int) -> str:
        amplitude = value / 255 * 1.65
        return f"{amplitude:1.3f} V"


class Frequency(Slider):
    def __init__(self):
        super().__init__("Frequency")

        self.slider.setMaximum(len(sine_table) - 1)

    @staticmethod
    def format_number(value: int) -> str:
        if value < 10:
            return f"{value:1.2f} Hz"
        if value < 100:
            return f"{value:2.1f} Hz"
        if value < 1_000:
            return f"{value:3.0f} Hz"
        if value < 10_000:
            return f"{value / 1e3:1.2f} kHz"

        return f"{value / 1e3:2.1f} kHz"

    def format_value(self, value: int) -> str:
        freq, sample_rate, points = sine_table[value]
        return self.format_number(freq)


class Multiplier(Slider):
    def __init__(self):
        super().__init__("Frequency multiplier")

        self.slider.setMaximum(20)


class SignalWidget(QWidget):
    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.changed = False

        parameter_layout = QGridLayout()

        self.function = Function()
        self.amplitude = Amplitude()
        self.lenlab.dac_lock.locked.connect(self.amplitude.set_disabled)
        self.frequency = Frequency()
        self.lenlab.dac_lock.locked.connect(self.frequency.set_disabled)
        self.harmonic = Multiplier()
        self.lenlab.dac_lock.locked.connect(self.harmonic.set_disabled)

        parameters: list[Parameter] = [
            self.function,
            self.amplitude,
            self.frequency,
            Parameter("Second signal"),
            self.harmonic,
        ]

        for row, parameter in enumerate(parameters):
            parameter.changed.connect(self.on_parameter_changed)
            for col, widget in enumerate(parameter.widgets()):
                parameter_layout.addWidget(widget, row, col)

        parameter_layout.setColumnStretch(2, 1)

        self.setLayout(parameter_layout)

        self.lenlab.lock.locked.connect(self.attempt_to_send)

    def create_command(self):
        frequency, sample_rate, length = sine_table[self.frequency.get_value()]

        harmonic = self.harmonic.get_value()
        if harmonic:
            harmonic_amplitude = amplitude = self.amplitude.get_value() // 2
        else:
            amplitude = self.amplitude.get_value()
            harmonic_amplitude = 0

        return command(
            b"s",
            sample_rate,
            length,
            amplitude,
            harmonic,
            harmonic_amplitude,
        )

    @Slot()
    def on_parameter_changed(self):
        # ignore calls due to reset to zero
        if self.lenlab.dac_lock.is_locked:
            return

        self.changed = True
        self.attempt_to_send()

    @Slot()
    def attempt_to_send(self):
        if self.changed and not self.lenlab.lock.is_locked and not self.lenlab.dac_lock.is_locked:
            self.lenlab.send_command(self.create_command())
            self.changed = False
