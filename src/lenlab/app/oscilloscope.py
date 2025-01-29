from importlib import metadata

import numpy as np
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt, Slot
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
from ..launchpad.protocol import command
from ..launchpad.terminal import Terminal
from .checkbox import BoolCheckBox
from .signal import SignalWidget


class OscilloscopeChart(QWidget):
    labels = (
        "Channel 1 (PA 24)",
        "Channel 2 (PA 17)",
    )

    x_label = "time [ms]"
    y_label = "voltage [V]"

    def __init__(self):
        super().__init__()

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart = self.chart_view.chart()
        # chart.setTheme(QChart.ChartTheme.ChartThemeLight)  # default, grid lines faint
        # chart.setTheme(QChart.ChartTheme.ChartThemeDark)  # odd gradient
        # chart.setTheme(QChart.ChartTheme.ChartThemeBlueNcs)  # grid lines faint
        self.chart.setTheme(
            QChart.ChartTheme.ChartThemeQt
        )  # light and dark green, stronger grid lines

        self.x_axis = QValueAxis()
        self.x_axis.setRange(-1.5, 1.5)
        self.x_axis.setTickCount(7)
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText(self.x_label)
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(-2.0, 2.0)
        self.y_axis.setTickCount(5)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText(self.y_label)
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        self.channels = [QLineSeries() for _ in self.labels]
        for channel, label in zip(self.channels, self.labels, strict=True):
            channel.setName(str(label))
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(self.y_axis)

        layout = QHBoxLayout()
        layout.addWidget(self.chart_view)
        self.setLayout(layout)

    def replace(self, interval_ms, time, channel_1, channel_2):
        for channel, values in zip(self.channels, [channel_1, channel_2], strict=False):
            channel.replace(list(map(QPointF, time, values)))

        self.x_axis.setRange(-3e3 * interval_ms, 3e3 * interval_ms)


class OscilloscopeWidget(QWidget):
    title = "Oscilloscope"

    sample_rates = ["2 MHz", "1 MHz", "500 kHz", "250 kHz"]
    intervals_100ns = [5, 10, 20, 40]

    terminal: Terminal

    time: np.ndarray
    ch1: np.ndarray
    ch2: np.ndarray

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.time = np.ndarray((0,))
        self.ch1 = np.ndarray((0,))
        self.ch2 = np.ndarray((0,))

        chart_layout = QVBoxLayout()

        self.chart = OscilloscopeChart()
        chart_layout.addWidget(self.chart, 1)

        self.signal = SignalWidget(lenlab)
        chart_layout.addWidget(self.signal)

        sidebar_layout = QVBoxLayout()

        # sampling rate
        layout = QHBoxLayout()

        label = QLabel("Sample rate")
        layout.addWidget(label)

        self.sample_rate = QComboBox()
        for sample_rate in self.sample_rates:
            self.sample_rate.addItem(sample_rate)

        layout.addWidget(self.sample_rate)

        sidebar_layout.addLayout(layout)

        # start
        layout = QHBoxLayout()

        button = QPushButton("Single")
        button.clicked.connect(self.on_start_clicked)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        # channels
        checkboxes = [BoolCheckBox(label) for label in self.chart.labels]

        for checkbox, channel in zip(checkboxes, self.chart.channels, strict=True):
            checkbox.setChecked(True)
            checkbox.check_changed.connect(channel.setVisible)
            sidebar_layout.addWidget(checkbox)

        # save as
        layout = QHBoxLayout()

        button = QPushButton("Save as")
        button.clicked.connect(self.on_save_as_clicked)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        sidebar_layout.addStretch(1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(chart_layout, stretch=1)
        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

        self.lenlab.reply.connect(self.on_reply)

    @Slot()
    def on_start_clicked(self):
        index = self.sample_rate.currentIndex()
        interval = self.intervals_100ns[index]
        self.lenlab.send_command(command(b"a", interval))

    @Slot(bytes)
    def on_reply(self, reply):
        if reply.startswith(b"La") or reply.startswith(b"Lb"):
            payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)
            interval_100ns = int.from_bytes(reply[4:8], byteorder="little")
            interval_ms = interval_100ns * 1e-4

            # 12 bit signed binary (2s complement), left aligned
            payload = payload >> 4

            data = payload.astype(np.float64)
            data = data * 3.3 / 4096  # 12 bit signed ADC

            length = data.shape[0] // 2  # 2 channels
            half = length / 2

            # ms
            self.time = np.linspace(-half, half, length, endpoint=False) * interval_ms
            self.ch1 = data[:length]
            self.ch2 = data[length:]

            self.chart.replace(interval_ms, self.time, self.ch1, self.ch2)

    @Slot()
    def on_save_as_clicked(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self,
            "Save Oscilloscope Data",
            "lenlab_osci.csv",
            "CSV (*.csv)",
        )
        if not file_name:  # cancelled
            return

        self.save_as(file_name)

    def save_as(self, file_name: str):
        with open(file_name, "w") as file:
            version = metadata.version("lenlab")
            file.write(f"Lenlab MSPM0 {version} Oscilloscope\n")
            file.write("Zeit; Kanal_1; Kanal_2\n")
            for t, ch1, ch2 in zip(self.time, self.ch1, self.ch2, strict=False):
                file.write(f"{t:f}; {ch1:f}; {ch2:f}\n")
