from itertools import batched

import numpy as np
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QLogValueAxis, QValueAxis
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller.signal import sine_table
from ..launchpad.discovery import Discovery
from ..launchpad.protocol import command
from ..launchpad.terminal import Terminal


class BodeChart(QWidget):
    labels = (
        "Magnitude",
        "Phase",
    )

    x_label = "frequency [Hz]"
    m_label = "magnitude [dB]"
    p_label = "phase [π]"

    terminal: Terminal

    def __init__(self, discovery: Discovery):
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

        self.x_axis = QLogValueAxis()
        self.x_axis.setBase(10)
        self.x_axis.setRange(1e2, 1e4)
        self.x_axis.setMinorTickCount(-1)  # automatic
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText(self.x_label)
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.m_axis = QValueAxis()
        self.m_axis.setRange(-40.0, 10.0)
        self.m_axis.setTickCount(6)
        self.m_axis.setLabelFormat("%g")
        self.m_axis.setTitleText(self.m_label)
        self.chart.addAxis(self.m_axis, Qt.AlignmentFlag.AlignLeft)

        self.p_axis = QValueAxis()
        self.p_axis.setRange(-2.0, 1.0)
        self.p_axis.setTickCount(7)  # 6 intervals
        self.p_axis.setMinorTickCount(4)  # 5 intervals
        self.p_axis.setLabelFormat("%g")
        self.p_axis.setTitleText(self.p_label)
        self.chart.addAxis(self.p_axis, Qt.AlignmentFlag.AlignRight)

        self.channels = [QLineSeries() for _ in self.labels]
        axes = [self.m_axis, self.p_axis]
        for channel, label, axis in zip(self.channels, self.labels, axes, strict=True):
            channel.setName(str(label))
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(axis)

        layout = QHBoxLayout()
        layout.addWidget(self.chart_view)
        self.setLayout(layout)

        discovery.ready.connect(self.on_ready)

    @Slot(Terminal)
    def on_ready(self, terminal):
        self.terminal = terminal
        self.terminal.reply.connect(self.on_reply)

    def averages_by_sample_rate(self, sample_rate: int):
        if sample_rate == 200:
            return 4
        if sample_rate == 500:
            return 2
        else:
            return 1

    def measure(self, index=0):
        self.index = index
        freq, sample_rate, length = sine_table[self.index]
        self.terminal.write(
            command(
                b"s",
                sample_rate,
                length,
                1862,  # 1.5 V
            )
        )

    @Slot(bytes)
    def on_reply(self, reply):
        if reply.startswith(b"Ls"):
            freq, sample_rate, length = sine_table[self.index]
            averages = self.averages_by_sample_rate(sample_rate)
            self.terminal.write(command(b"a", averages))

        elif reply.startswith(b"La"):
            payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)
            averages = int.from_bytes(reply[4:8], byteorder="little")

            # 12 bit signed binary (2s complement), left aligned
            payload = payload >> 4

            data = payload.astype(np.float64)
            data = data * 3.3 / 4096  # 12 bit signed ADC

            length = data.shape[0] // 2  # 2 channels
            ch1, ch2 = batched(data, length)

            f = sine_table[self.index][0]
            o = length / 2

            x = 2 * np.pi * f * np.linspace(-o, o, length, endpoint=False) * averages / 2e6
            y = np.sin(x) + 1j * np.cos(x)
            transfer = np.sum(y * ch2) / np.sum(y * ch1)

            magnitude = 20 * np.log10(np.absolute(transfer))
            phase = np.angle(transfer)

            self.channels[0].append(f, magnitude)
            self.channels[1].append(f, phase)

            index = self.index + 2
            if index < len(sine_table):
                self.measure(self.index + 1)


class BodeWidget(QWidget):
    title = "Bode Plotter"

    terminal: Terminal

    def __init__(self, discovery: Discovery):
        super().__init__()

        sidebar_layout = QVBoxLayout()

        # sampling rate
        layout = QHBoxLayout()

        # start
        layout = QHBoxLayout()

        button = QPushButton("Start")
        button.clicked.connect(self.on_start_clicked)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)
        sidebar_layout.addStretch(1)

        main_layout = QHBoxLayout()

        self.chart = BodeChart(discovery)
        main_layout.addWidget(self.chart, stretch=1)

        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

    @Slot()
    def on_start_clicked(self):
        self.chart.measure()
