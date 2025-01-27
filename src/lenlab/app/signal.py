from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QSlider, QWidget

from ..controller.signal import sine_table
from ..launchpad.discovery import Discovery
from ..launchpad.protocol import command
from ..launchpad.terminal import Terminal


class Parameter(QObject):
    changed = Signal()

    value: int

    def __init__(self):
        super().__init__()

        self.value = 0

        self.label = QLabel()
        self.field = QLineEdit()
        self.slider = QSlider(Qt.Orientation.Horizontal)

        self.field.setText(self.format_value(0))

        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.on_slider_value_changed)

    def widgets(self):
        yield self.label
        yield self.field
        yield self.slider

    def format_value(self, value: int) -> str:
        return str(value)

    @Slot(int)
    def on_slider_value_changed(self, value):
        self.field.setText(self.format_value(value))
        self.value = value
        self.changed.emit()


class Frequency(Parameter):
    def __init__(self):
        super().__init__()

        self.label.setText("Frequency")

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
        f = sine_table[value][0]
        return self.format_number(f)


class Amplitude(Parameter):
    def __init__(self, label: str = "Amplitude"):
        super().__init__()

        self.label.setText(label)
        self.slider.setMaximum(2048)

    def format_value(self, value: int) -> str:
        amplitude = value / 2048 * 1.65
        return f"{amplitude:1.3f} V"


class Multiplier(Parameter):
    def __init__(self):
        super().__init__()

        self.label.setText("Harmonic\nMultiplier")
        self.slider.setMaximum(20)


class SignalWidget(QWidget):
    terminal: Terminal

    def __init__(self, discovery: Discovery):
        super().__init__()

        self.busy = True

        layout = QGridLayout()

        self.frequency = Frequency()
        self.amplitude = Amplitude()
        self.harmonic = Multiplier()
        self.harmonic_amplitude = Amplitude("Harmonic\nAmplitude")

        parameters: list[Parameter] = [
            self.frequency,
            self.amplitude,
            self.harmonic,
            self.harmonic_amplitude,
        ]

        for row, parameter in enumerate(parameters):
            parameter.changed.connect(self.on_parameter_changed)
            for col, widget in enumerate(parameter.widgets()):
                layout.addWidget(widget, row, col)

        layout.setColumnStretch(2, 1)

        self.setLayout(layout)

        discovery.ready.connect(self.on_ready)

    @Slot(Terminal)
    def on_ready(self, terminal):
        self.terminal = terminal
        self.terminal.reply.connect(self.on_reply)
        self.busy = False

    @Slot(bytes)
    def on_reply(self, reply):
        if reply.startswith(b"Ls"):
            self.busy = False

    @Slot()
    def on_parameter_changed(self):
        if not self.busy:
            self.busy = True

            sample_rate = sine_table[self.frequency.value][1]
            length = sine_table[self.frequency.value][2]
            self.terminal.write(
                command(
                    b"s",
                    sample_rate,
                    length,
                    self.amplitude.value,
                    self.harmonic.value,
                    self.harmonic_amplitude.value,
                )
            )
