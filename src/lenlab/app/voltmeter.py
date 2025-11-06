import logging

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller.lenlab import Lenlab
from ..launchpad.protocol import command
from ..model.points import Points
from ..translate import Translate, tr
from .checkbox import BoolCheckBox
from .save_as import SaveAs

logger = logging.getLogger(__name__)


class VoltmeterChart(QWidget):
    labels = (
        Translate("Channel 1 (ADC 0, PA 24)", "Kanal 1 (ADC 0, PA 24)"),
        Translate("Channel 2 (ADC 1, PA 17)", "Kanal 2 (ADC 1, PA 17)"),
    )

    x_label = Translate("time [s]", "Zeit [s]")
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
        self.x_axis.setRange(0.0, 4.0)
        self.x_axis.setTickCount(5)
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText(str(self.x_label))
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(0.0, 4.0)
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

    limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0]

    @classmethod
    def get_time_limit(cls, value: float) -> float:
        for x in cls.limits:
            if x >= value:
                return x

        return cls.limits[-1]

    @staticmethod
    def get_time_unit(value: float) -> int:
        if value <= 2.0 * 60.0:  # 2 minutes
            return 1  # seconds
        elif value <= 2 * 60.0 * 60.0:  # 2 hours
            return 60  # minutes
        else:
            return 60 * 60  # hours

    def plot(self, points: Points):
        unit = self.get_time_unit(points.get_current_time())
        time = points.get_plot_time(unit)

        # channel.replaceNp iterates over the raw c-array
        # and copies the values into a QList<QPointF>
        # It cannot read views or strides
        for i, channel in enumerate(self.channels):
            channel.replaceNp(time, points.get_plot_values(i))

        self.x_axis.setMax(self.get_time_limit(points.get_current_time() / unit))


class VoltmeterWidget(QWidget):
    title = Translate("Voltmeter", "Voltmeter")

    intervals = [20, 50, 100, 200, 500, 1000, 2000, 5000]

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        # poll interval
        self.poll_timer = QTimer()
        self.poll_timer.setSingleShot(True)
        self.poll_timer.timeout.connect(self.on_poll_timeout)

        chart_layout = QVBoxLayout()

        self.chart = VoltmeterChart()
        chart_layout.addWidget(self.chart, 1)

        sidebar_layout = QVBoxLayout()

        # interval
        self.interval = QComboBox()
        for interval in self.intervals:
            self.interval.addItem(f"{interval} ms")
        self.interval.setCurrentIndex(self.intervals.index(1000))
        # self.voltmeter.active_changed.connect(self.interval.setDisabled)

        layout = QHBoxLayout()

        label = QLabel(tr("Interval", "Intervall"))
        layout.addWidget(label)
        layout.addWidget(self.interval)

        sidebar_layout.addLayout(layout)

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

        # time
        label = QLabel(tr("Time", "Zeit"))
        sidebar_layout.addWidget(label)

        self.time_field = QLineEdit()
        self.time_field.setReadOnly(True)
        sidebar_layout.addWidget(self.time_field)

        # channels
        checkboxes = [BoolCheckBox(label) for label in self.chart.labels]
        self.fields = [QLineEdit() for _ in self.chart.labels]

        for (
            checkbox,
            field,
            channel,
        ) in zip(checkboxes, self.fields, self.chart.channels, strict=True):
            checkbox.setChecked(True)
            checkbox.check_changed.connect(channel.setVisible)
            sidebar_layout.addWidget(checkbox)

            field.setReadOnly(True)
            sidebar_layout.addWidget(field)

        # save as
        button = QPushButton(tr("Save as", "Speichern unter"))
        button.clicked.connect(self.on_save_as_clicked)
        self.lenlab.adc_lock.locked.connect(button.setDisabled)
        sidebar_layout.addWidget(button)

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        sidebar_layout.addWidget(self.file_name)

        self.auto_save = BoolCheckBox(tr("Automatic saving", "Automatisch speichern"))
        self.auto_save.setEnabled(False)
        # self.auto_save.check_changed.connect(self.voltmeter.set_auto_save)
        # set_auto_save might cause a change back in case of an error
        # self.voltmeter.auto_save_changed.connect(
        #     self.auto_save.setChecked, Qt.ConnectionType.QueuedConnection
        # )
        sidebar_layout.addWidget(self.auto_save)

        button = QPushButton(tr("Save image", "Bild speichern"))
        # button.clicked.connect(self.on_save_image_clicked)
        sidebar_layout.addWidget(button)

        button = QPushButton(tr("Discard", "Verwerfen"))
        # self.voltmeter.active_changed.connect(button.setDisabled)
        # button.clicked.connect(self.on_discard_clicked)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(chart_layout, stretch=1)
        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

        self.lenlab.reply.connect(self.on_reply)

    @Slot()
    def on_start_clicked(self):
        if self.lenlab.adc_lock.acquire():
            index = self.interval.currentIndex()
            interval_25ns = self.intervals[index] * 40_000
            self.points = Points(self.intervals[index] / 1000)
            self.lenlab.send_command(command(b"v", interval_25ns))

    @Slot()
    def on_stop_clicked(self):
        self.poll_timer.stop()
        self.lenlab.send_command(command(b"x"))

    @Slot()
    def on_poll_timeout(self):
        self.lenlab.send_command(command(b"v"))

    @Slot(bytes)
    def on_reply(self, reply):
        if reply.startswith(b"Lv") or reply.startswith(b"Lu"):
            length = int.from_bytes(reply[2:4], byteorder="little")

            if length == 0:  # start or empty poll
                interval_25ns = int.from_bytes(reply[4:8], byteorder="little")
                interval_ms = max(200, interval_25ns // 40_000)
                self.poll_timer.setInterval(interval_ms)

            else:  # new points
                self.points.parse_reply(reply)
                self.chart.plot(self.points)

            self.poll_timer.start()

        elif reply == b"Lx\x00\x00stop":
            self.lenlab.adc_lock.release()

    @Slot()
    @SaveAs(
        tr("Save Voltmeter Data", "Voltmeter-Daten speichern"),
        "lenlab_volt.csv",
        "CSV (*.csv)",
    )
    def on_save_as_clicked(self, file_name: str, file_format: str):
        pass
        # with open(file_name, "w") as file:
        #     self.chart.waveform.save_as(file)
