from importlib import metadata

import numpy as np
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QLogValueAxis, QValueAxis
from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller.lenlab import Lenlab
from ..controller.signal import sine_table
from ..launchpad.protocol import command


class BodeChart(QWidget):
    labels = (
        "Magnitude",
        "Phase",
    )

    x_label = "frequency [Hz]"
    m_label = "magnitude [dB]"
    p_label = "phase [deg]"

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
        self.x_axis.setTitleText(self.x_label)
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.m_axis = QValueAxis()
        self.m_axis.setRange(-50.0, 10.0)
        self.m_axis.setTickCount(7)
        self.m_axis.setLabelFormat("%g")
        self.m_axis.setTitleText(self.m_label)
        self.chart.addAxis(self.m_axis, Qt.AlignmentFlag.AlignLeft)

        self.p_axis = QValueAxis()
        self.p_axis.setRange(-360.0, 180.0)
        self.p_axis.setTickCount(7)  # 6 intervals
        self.p_axis.setMinorTickCount(4)  # 5 intervals
        self.p_axis.setLabelFormat("%g")
        self.p_axis.setTitleText(self.p_label)
        self.chart.addAxis(self.p_axis, Qt.AlignmentFlag.AlignRight)

        axes = [self.m_axis, self.p_axis]
        for channel, label, axis in zip(self.channels, self.labels, axes, strict=True):
            channel.setName(str(label))
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(axis)

        layout = QHBoxLayout()
        layout.addWidget(self.chart_view)
        self.setLayout(layout)


class BodeWidget(QWidget):
    title = "Bode Plotter"

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
        layout = QHBoxLayout()

        button = QPushButton("Save as")
        button.clicked.connect(self.on_save_as_clicked)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        sidebar_layout.addStretch(1)

        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

    @Slot()
    def on_start_clicked(self):
        self.bode.start(step=1 << self.samples.currentIndex())

    @Slot()
    def on_save_as_clicked(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self,
            "Save Bode Plot",
            "lenlab_bode.csv",
            "CSV (*.csv)",
        )
        if not file_name:  # cancelled
            return

        self.bode.save_as(file_name)


class BodePlotter(QObject):
    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.active = False
        self.index = 0
        self.step = 1
        self.magnitude = QLineSeries()
        self.phase = QLineSeries()

    @staticmethod
    def interval_by_sample_rate(sample_rate: int):
        if sample_rate == 200:
            return 20
        if sample_rate == 500:
            return 10
        else:
            return 5

    @Slot(bool)
    def on_ready(self, ready):
        self.active = False

    def start(self, step: int):
        if self.active:
            return

        if not self.lenlab.dac_lock.acquire():
            return

        if not self.lenlab.adc_lock.acquire():
            self.lenlab.dac_lock.release()
            return

        self.active = True

        self.magnitude.clear()
        self.phase.clear()

        self.index = 0
        self.step = step

        self.measure()

    @Slot()
    def stop(self):
        self.active = False

    def measure(self):
        freq, sample_rate, length = sine_table[self.index]
        interval = self.interval_by_sample_rate(sample_rate)
        self.lenlab.send_command(
            command(
                b"b",
                sample_rate,
                length,
                1862,  # 1.5 V
                interval,
            )
        )

    @Slot(int, object, object)
    def on_bode(self, interval_100ns, channel_1, channel_2):
        interval = interval_100ns * 100e-9  # seconds
        f = sine_table[self.index][0]  # hertz
        length = channel_1.shape[0]

        x = 2 * np.pi * f * np.linspace(0, interval * length, length, endpoint=False)
        y = np.sin(x) + 1j * np.cos(x)
        transfer = np.sum(y * channel_2) / np.sum(y * channel_1)

        magnitude = 20 * np.log10(np.absolute(transfer))
        angle = np.angle(transfer) / np.pi * 180.0

        prev = self.phase.at(self.phase.count() - 1).y() if self.phase.count() else 0
        phase = np.unwrap((prev, angle), period=360.0)[1]  # remove jumps by 2 pi

        self.magnitude.append(float(f), float(magnitude))
        self.phase.append(float(f), float(phase))

        self.index += self.step
        if self.active and self.index < len(sine_table):
            self.measure()
        else:
            self.active = False

            self.lenlab.dac_lock.release()
            self.lenlab.adc_lock.release()

    def save_as(self, file_name: str):
        with open(file_name, "w") as file:
            version = metadata.version("lenlab")
            file.write(f"Lenlab MSPM0 {version} Bode\n")
            file.write("Frequenz; Betrag; Phase\n")
            for m, p in zip(self.magnitude.points(), self.phase.points(), strict=False):
                file.write(f"{m.x():.0f}; {m.y():f}; {p.y():f}\n")
