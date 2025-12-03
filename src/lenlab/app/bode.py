from pathlib import Path
from typing import TextIO

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import TABLEAU_COLORS
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QLogValueAxis, QValueAxis
from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..controller.csv import CSVTemplate
from ..controller.lenlab import Lenlab
from ..controller.signal import sine_table
from ..launchpad.protocol import command
from ..message import Message
from ..translate import Translate, tr
from .save_as import SaveAs


class BodeChart(QWidget):
    labels = (
        Translate("Magnitude", "Betrag"),
        Translate("Phase", "Phase"),
    )

    colors = (
        TABLEAU_COLORS["tab:blue"],
        TABLEAU_COLORS["tab:orange"],
    )

    x_label = Translate("frequency [Hz]", "Frequenz [Hz]")
    m_label = Translate("magnitude [dB]", "Betrag [dB]")
    p_label = Translate("phase [°]", "Phase [°]")

    def __init__(self, channels: list[QLineSeries]):
        super().__init__()
        self.channels = channels

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart = self.chart_view.chart()
        # chart.setTheme(QChart.ChartTheme.ChartThemeLight)  # default, grid lines faint
        # chart.setTheme(QChart.ChartTheme.ChartThemeDark)  # odd gradient
        # chart.setTheme(QChart.ChartTheme.ChartThemeBlueNcs)  # grid lines faint
        self.chart.setTheme(
            QChart.ChartTheme.ChartThemeQt
        )  # light and dark green, stronger grid lines

        self.x_axis = QLogValueAxis()
        self.x_axis.setBase(10)
        self.x_axis.setRange(1e2, 1e4)
        self.x_axis.setMinorTickCount(-1)  # automatic
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText(str(self.x_label))
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.m_axis = QValueAxis()
        self.m_axis.setRange(-50.0, 10.0)
        self.m_axis.setTickCount(7)
        self.m_axis.setLabelFormat("%g")
        self.m_axis.setTitleText(str(self.m_label))
        self.chart.addAxis(self.m_axis, Qt.AlignmentFlag.AlignLeft)

        self.p_axis = QValueAxis()
        self.p_axis.setRange(-360.0, 180.0)
        self.p_axis.setTickCount(7)  # 6 intervals
        self.p_axis.setMinorTickCount(4)  # 5 intervals
        self.p_axis.setLabelFormat("%g")
        self.p_axis.setTitleText(str(self.p_label))
        self.chart.addAxis(self.p_axis, Qt.AlignmentFlag.AlignRight)

        axes = [self.m_axis, self.p_axis]
        for channel, label, color, axis in zip(
            self.channels, self.labels, self.colors, axes, strict=True
        ):
            channel.setName(str(label))
            channel.setPen(QPen(QColor.fromString(color)))
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(axis)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chart_view)
        self.setLayout(layout)


class BodeWidget(QWidget):
    title = Translate("Bode Plotter", "Bode-Plotter")

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.bode = BodePlotter(lenlab)
        self.lenlab.ready.connect(self.bode.on_ready)

        main_layout = QHBoxLayout()

        self.chart = BodeChart([self.bode.magnitude, self.bode.phase])
        main_layout.addWidget(self.chart, stretch=1)

        sidebar_layout = QVBoxLayout()

        # samples
        layout = QHBoxLayout()

        label = QLabel("Samples")
        layout.addWidget(label)

        self.samples = QComboBox()
        for choice in [200, 100, 50, 25]:
            self.samples.addItem(str(choice))

        self.samples.setCurrentIndex(1)
        layout.addWidget(self.samples)

        sidebar_layout.addLayout(layout)

        # amplitude
        layout = QHBoxLayout()

        label = QLabel("Amplitude")
        layout.addWidget(label)

        self.amplitude = QComboBox()
        for choice in ["1.5 V", "1.4 V", "1.3 V", "1.2 V", "1.1 V", "1.0 V"]:
            self.amplitude.addItem(str(choice))

        layout.addWidget(self.amplitude)

        sidebar_layout.addLayout(layout)

        # start / stop
        layout = QHBoxLayout()

        button = QPushButton("Start")
        button.setEnabled(False)
        button.clicked.connect(self.on_start_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        layout.addWidget(button)

        button = QPushButton("Stop")
        button.clicked.connect(self.bode.stop)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        # save as
        button = QPushButton(tr("Save as", "Speichern unter"))
        button.clicked.connect(self.on_save_as_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        sidebar_layout.addWidget(button)

        button = QPushButton(tr("Save image", "Bild speichern"))
        button.clicked.connect(self.on_save_image_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        sidebar_layout.addWidget(button)

        # pin assignment

        label = QLabel()
        label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        label.setTextFormat(Qt.TextFormat.MarkdownText)
        label.setWordWrap(True)
        label.setText(PinAssignment().long_form())

        sidebar_layout.addWidget(label)

        sidebar_layout.addStretch(1)

        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

    @Slot()
    def on_start_clicked(self):
        step = 1 << self.samples.currentIndex()
        amplitude = 1.5 - 0.1 * self.amplitude.currentIndex()
        self.bode.start(step, amplitude)

    @Slot()
    def on_save_as_clicked(self):
        dialog = SaveAs(self)
        dialog.setWindowTitle(tr("Save bode plot", "Bode-Plot speichern"))
        dialog.set_default_file_name("lenlab_bode.csv")
        dialog.on_save_as = self.on_save_as
        dialog.open()

    def on_save_as(self, file_path: Path):
        with file_path.open("w", encoding="utf-8", newline="\n") as file:
            self.bode.save_as(file)

    @Slot()
    def on_save_image_clicked(self):
        dialog = SaveAs(self)
        dialog.setWindowTitle(tr("Save bode plot (image)", "Bode-Plot (Bild) speichern"))
        dialog.set_default_file_name("lenlab_bode.svg")
        dialog.on_save_as = self.bode.save_image
        dialog.open()


class BodePlotter(QObject):
    dac_per_volt = 4096 / 3.3

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.active = False
        self.index = 0
        self.step = 1
        self.amplitude = 1.5
        self.magnitude = QLineSeries()
        self.phase = QLineSeries()

    @Slot(bool)
    def on_ready(self, ready):
        self.active = False

    def start(self, step: int, amplitude: float):
        if self.active:
            return

        if not self.lenlab.adc_lock.acquire():
            return

        self.active = True

        self.magnitude.clear()
        self.phase.clear()

        self.index = 0
        self.step = step
        self.amplitude = amplitude

        self.measure()

    @Slot()
    def stop(self):
        self.active = False

    def measure(self):
        frequency_hertz, interval_25ns, points = sine_table[self.index]
        amplitude = int(self.amplitude * self.dac_per_volt)
        self.lenlab.send_command(
            command(
                b"b",
                interval_25ns,
                points,
                amplitude,
            )
        )

    @Slot(object)
    def on_bode(self, waveform):
        frequency_hertz, interval_25ns, points = sine_table[self.index]

        t = np.linspace(0, waveform.length, waveform.length, endpoint=False) * waveform.time_step
        x = 2 * np.pi * frequency_hertz * t
        y = np.sin(x) + 1j * np.cos(x)
        transfer = np.sum(y * waveform.channels[1]) / np.sum(y * waveform.channels[0])

        magnitude = 20 * np.log10(np.absolute(transfer))
        angle = np.angle(transfer) / np.pi * 180.0

        prev = self.phase.at(self.phase.count() - 1).y() if self.phase.count() else 0
        phase = np.unwrap((prev, angle), period=360.0)[1]  # remove jumps by 2 pi

        self.magnitude.append(float(frequency_hertz), float(magnitude))
        self.phase.append(float(frequency_hertz), float(phase))

        self.index += self.step
        if self.active and self.index < len(sine_table):
            self.measure()
        else:
            self.active = False
            self.lenlab.adc_lock.release()

    def rows(self):
        return (
            (m.x(), m.y(), p.y())
            for m, p in zip(self.magnitude.points(), self.phase.points(), strict=True)
        )

    csv_template = CSVTemplate("bode_plot", "frequency", "magnitude", "phase", ".0f")

    def save_as(self, file: TextIO):
        file.write(self.csv_template.head())
        self.csv_template.write_rows(file.write, self.rows())

    def save_image(self, file_path: Path):
        fig, ax = plt.subplots(figsize=[12.8, 9.6], dpi=150)

        ax1 = ax.twinx()

        ax.set_xlim(1e2, 1e4)
        ax.set_ylim(-50, 10)
        ax1.set_ylim(-360, 180)
        ax1.set_yticks(list(range(-360, 181, 90)))

        ax.set_xlabel(str(BodeChart.x_label))
        ax.set_ylabel(str(BodeChart.m_label))
        ax1.set_ylabel(str(BodeChart.p_label))

        f = [m.x() for m in self.magnitude.points()]
        m = [m.y() for m in self.magnitude.points()]
        p = [p.y() for p in self.phase.points()]

        ax.minorticks_on()
        ax.grid()
        ax.grid(which="minor")
        lines = ax.semilogx(f, m, "C0", label=str(BodeChart.labels[0])) + ax1.semilogx(
            f, p, "C1", label=str(BodeChart.labels[1])
        )

        ax.legend(lines, [x.get_label() for x in lines])

        fig.savefig(file_path)


class PinAssignment(Message):
    english = """### Pin Assignment
    
    #### Filter input 

    - ADC 0, PA 24
    - DAC, PA 15
    
    #### Filter output
    
    - ADC 1, PA 17
    """
    german = """### Pin-Belegung
    
    #### Filtereingang:
    
    - ADC 0, PA 24
    - DAC, PA 15
    
    #### Filterausgang:
    
    - ADC 1, PA 17
    """
