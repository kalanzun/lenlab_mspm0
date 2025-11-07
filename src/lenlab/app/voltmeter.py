import logging
from datetime import timedelta

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

from ..controller.auto_save import AutoSave
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

    x_label = Translate("time [{0}]", "Zeit [{0}]")
    y_label = Translate("voltage [volt]", "Spannung [Volt]")

    unit_labels = {
        1: Translate("seconds", "Sekunden"),
        60: Translate("minutes", "Minuten"),
        60 * 60: Translate("hours", "Stunden"),
    }

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
        self.x_axis.setTitleText(str(self.x_label).format(self.unit_labels[1]))
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

    @staticmethod
    def get_time_limit(value: float) -> float:
        limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0]
        for x in limits:
            if x >= value:
                return x

        return limits[-1]

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
        self.x_axis.setTitleText(str(self.x_label).format(self.unit_labels[unit]))


class VoltmeterWidget(QWidget):
    title = Translate("Voltmeter", "Voltmeter")

    intervals = [20, 50, 100, 200, 500, 1000, 2000, 5000]

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.auto_save = AutoSave()

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
            checkbox.check_changed.connect(field.clear)
            checkbox.check_changed.connect(field.setEnabled)
            sidebar_layout.addWidget(checkbox)

            field.setReadOnly(True)
            sidebar_layout.addWidget(field)

        # save as
        button = QPushButton(tr("Save as", "Speichern unter"))
        button.clicked.connect(self.on_save_as_clicked)
        sidebar_layout.addWidget(button)

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        self.auto_save.file_name_changed.connect(self.file_name.setText)
        sidebar_layout.addWidget(self.file_name)

        checkbox = BoolCheckBox(tr("Automatic saving", "Automatisch speichern"))
        # self.auto_save_check_box.setEnabled(False)
        checkbox.check_changed.connect(self.auto_save.set_auto_save)
        # set_auto_save might cause a change back in case of an error
        self.auto_save.auto_save_changed.connect(
            checkbox.setChecked, Qt.ConnectionType.QueuedConnection
        )
        sidebar_layout.addWidget(checkbox)

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
            self.auto_save.set_points(self.points)
            self.lenlab.send_command(command(b"v", interval_25ns))

    @Slot()
    def on_stop_clicked(self):
        self.poll_timer.stop()
        self.lenlab.send_command(command(b"x"))

    @Slot()
    def on_poll_timeout(self):
        self.lenlab.send_command(command(b"v"))

    @staticmethod
    def format_time(time: float, show_ms: bool = True) -> str:
        td = timedelta(seconds=time)
        if td.microseconds:
            return str(td)[:-4]
        elif show_ms:
            return f"{td}.00"
        else:
            return str(td)

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
                self.auto_save.set_unsaved(True)

                self.chart.plot(self.points)
                self.auto_save.save()

                self.time_field.setText(
                    self.format_time(self.points.get_current_time(), self.points.interval < 1.0)
                )
                for i, field in enumerate(self.fields):
                    if field.isEnabled():
                        field.setText(f"{self.points.get_last_value(i):.3f} V")

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
        self.auto_save.save_as(file_name)
