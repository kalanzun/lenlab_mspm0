from itertools import batched

import numpy as np
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..launchpad.discovery import Discovery
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

    @Slot(bytes)
    def on_reply(self, reply):
        if reply.startswith(b"La"):
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
            time = np.linspace(-half, half, length, endpoint=False) * interval_ms

            for channel, values in zip(self.channels, batched(data, length), strict=False):
                channel.replace(list(map(QPointF, time, values)))

            self.x_axis.setRange(-3e3 * interval_ms, 3e3 * interval_ms)


class OscilloscopeWidget(QWidget):
    title = "Oscilloscope"

    sample_rates = ["2 MHz", "1 MHz", "500 kHz", "250 kHz"]
    intervals_100ns = [5, 10, 20, 40]

    terminal: Terminal

    def __init__(self, discovery: Discovery):
        super().__init__()

        chart_layout = QVBoxLayout()

        self.chart = OscilloscopeChart()
        chart_layout.addWidget(self.chart, 1)

        self.signal = SignalWidget(discovery)
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

        sidebar_layout.addStretch(1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(chart_layout, stretch=1)
        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

        discovery.ready.connect(self.on_ready)

    @Slot(Terminal)
    def on_ready(self, terminal):
        self.terminal = terminal
        self.terminal.reply.connect(self.chart.on_reply)

    @Slot()
    def on_start_clicked(self):
        index = self.sample_rate.currentIndex()
        interval = self.intervals_100ns[index]
        self.terminal.write(command(b"a", interval))
