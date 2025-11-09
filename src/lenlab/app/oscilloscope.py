import logging
from pathlib import Path

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller.lenlab import Lenlab
from ..model.waveform import Waveform
from ..translate import Translate, tr
from .checkbox import BoolCheckBox
from .save_as import SaveAs
from .signal import SignalWidget

logger = logging.getLogger(__name__)


class OscilloscopeChart(QWidget):
    labels = (
        Translate("Channel 1 (ADC 0, PA 24)", "Kanal 1 (ADC 0, PA 24)"),
        Translate("Channel 2 (ADC 1, PA 17)", "Kanal 2 (ADC 1, PA 17)"),
    )

    x_label = Translate("time [ms]", "Zeit [ms]")
    y_label = Translate("voltage [V]", "Spannung [V]")

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
        self.x_axis.setTitleText(str(self.x_label))
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(-2.0, 2.0)
        self.y_axis.setTickCount(5)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText(str(self.y_label))
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

    def plot(self, waveform: Waveform):
        time_ms = waveform.time_aligned() * 1e3
        for i, channel in enumerate(self.channels):
            channel.replaceNp(time_ms, waveform.channel_aligned(i))

        self.x_axis.setRange(-3e6 * waveform.time_step, 3e6 * waveform.time_step)


class OscilloscopeWidget(QWidget):
    title = Translate("Oscilloscope", "Oszilloskop")

    # sample_rates = ["4 MHz", "2 MHz", "1 MHz", "500 kHz", "250 kHz"]
    # intervals_25ns = [10, 20, 40, 80, 160]

    bode = Signal(object)

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.active = False
        self.waveform = Waveform()

        chart_layout = QVBoxLayout()

        self.chart = OscilloscopeChart()
        chart_layout.addWidget(self.chart, 1)

        self.signal = SignalWidget(lenlab)
        chart_layout.addWidget(self.signal)

        sidebar_layout = QVBoxLayout()

        # sample rate
        # layout = QHBoxLayout()

        # label = QLabel("Sample rate")
        # layout.addWidget(label)

        # self.sample_rate = QComboBox()
        # for sample_rate in self.sample_rates:
        #     self.sample_rate.addItem(sample_rate)

        # layout.addWidget(self.sample_rate)

        # sidebar_layout.addLayout(layout)

        # start / stop
        layout = QHBoxLayout()

        button = QPushButton("Start")
        button.setEnabled(False)
        button.clicked.connect(self.on_start_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        layout.addWidget(button)

        button = QPushButton("Stop")
        button.clicked.connect(self.on_stop_clicked)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        # single
        layout = QHBoxLayout()

        button = QPushButton("Single")
        button.setEnabled(False)
        button.clicked.connect(self.on_single_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        # channels
        checkboxes = [BoolCheckBox(label) for label in self.chart.labels]

        for checkbox, channel in zip(checkboxes, self.chart.channels, strict=True):
            checkbox.setChecked(True)
            checkbox.check_changed.connect(channel.setVisible)
            sidebar_layout.addWidget(checkbox)

        # save as
        button = QPushButton(tr("Save as", "Speichern unter"))
        button.clicked.connect(self.on_save_as_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(chart_layout, stretch=1)
        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

        self.lenlab.reply.connect(self.on_reply)

    def acquire(self):
        if self.lenlab.adc_lock.acquire():
            self.lenlab.send_command(self.signal.create_command(b"a"))
            return True

        return False

    @Slot()
    def on_start_clicked(self):
        if self.acquire():
            self.active = True

    @Slot()
    def on_stop_clicked(self):
        self.active = False

    @Slot()
    def on_single_clicked(self):
        self.acquire()

    @Slot(bytes)
    def on_reply(self, reply):
        if not (reply.startswith(b"La") or reply.startswith(b"Lb")):
            return

        if reply.startswith(b"La"):
            self.lenlab.adc_lock.release()

        self.waveform = Waveform.parse_reply(reply)
        self.chart.plot(self.waveform)

        if reply.startswith(b"La") and self.active:
            self.active = self.acquire()

        if reply.startswith(b"Lb"):
            self.bode.emit(self.waveform)

    @Slot()
    @SaveAs(
        tr("Save Oscilloscope Data", "Oszilloskop-Daten speichern"),
        "lenlab_osci.csv",
        "CSV (*.csv)",
    )
    def on_save_as_clicked(self, file_path: Path, file_format: str):
        self.waveform.save_as(file_path)
