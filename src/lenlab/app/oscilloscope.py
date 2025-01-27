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
            channels = np.frombuffer(reply, np.dtype("<i2"), offset=8)
            mid = channels.shape[0] // 2
            ch1 = channels[:mid]
            ch2 = channels[mid:]

            time_scale = 0.0005
            time_offset = -mid // 2 * time_scale
            scale = 10000

            self.channels[0].replace(
                [QPointF(time_offset + i * time_scale, y / scale) for i, y in enumerate(ch1)]
            )
            self.channels[1].replace(
                [QPointF(time_offset + i * time_scale, y / scale) for i, y in enumerate(ch2)]
            )


class OscilloscopeWidget(QWidget):
    title = "Oscilloscope"

    sampling_rates = ["2 MHz", "1 MHz", "500 kHz", "250 kHz"]

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

        label = QLabel("Sampling rate")
        layout.addWidget(label)

        self.sampling_rate = QComboBox()
        for sampling_rate in self.sampling_rates:
            self.sampling_rate.addItem(sampling_rate)

        layout.addWidget(self.sampling_rate)

        sidebar_layout.addLayout(layout)

        # start
        layout = QHBoxLayout()

        button = QPushButton("Start")
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
        index = self.sampling_rate.currentIndex()
        averages = 1 << index
        self.terminal.write(command(b"a", averages))
