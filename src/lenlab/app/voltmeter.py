import logging
import time
from itertools import batched

import matplotlib.pyplot as plt
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..message import Message
from ..model.lenlab import Lenlab
from ..model.voltmeter import Voltmeter, VoltmeterPoint
from .banner import MessageBanner
from .checkbox import BoolCheckBox

logger = logging.getLogger(__name__)


class VoltmeterWidget(QWidget):
    title = "Voltmeter"

    labels = ("Channel 1 (PA 24)", "Channel 2 (PA 17)")
    limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0]
    intervals = [20, 50, 100, 200, 500, 1000]

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab
        self.voltmeter = Voltmeter(lenlab)
        self.voltmeter.new_last_point.connect(
            self.on_new_last_point, Qt.ConnectionType.QueuedConnection
        )

        self.unit = 1  # second

        window_layout = QVBoxLayout()
        self.banner = MessageBanner("Dismiss")
        self.banner.retry_button.clicked.connect(self.banner.hide)
        self.voltmeter.error.connect(self.banner.set_error)
        window_layout.addWidget(self.banner)

        main_layout = QHBoxLayout()
        window_layout.addLayout(main_layout)

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
        self.x_axis.setTitleText(self.get_unit_label(self.unit))
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(0.0, 3.3)
        self.y_axis.setTickCount(5)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText("voltage [volts]")
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        self.channels = [QLineSeries() for _ in self.labels]
        for channel, label in zip(self.channels, self.labels, strict=True):
            channel.setName(label)
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(self.y_axis)

        main_layout.addWidget(self.chart_view, stretch=1)

        sidebar_layout = QVBoxLayout()
        main_layout.addLayout(sidebar_layout)

        # sample rate
        layout = QHBoxLayout()
        sidebar_layout.addLayout(layout)

        label = QLabel("Interval")
        layout.addWidget(label)

        self.interval = QComboBox()
        self.voltmeter.active_changed.connect(self.interval.setDisabled)
        layout.addWidget(self.interval)

        for interval in self.intervals:
            self.interval.addItem(f"{interval} ms")
        self.interval.setCurrentIndex(len(self.intervals) - 1)

        # start / stop
        layout = QHBoxLayout()
        sidebar_layout.addLayout(layout)

        button = QPushButton("Start")
        self.voltmeter.active_changed.connect(button.setDisabled)
        button.clicked.connect(self.on_start_clicked)
        layout.addWidget(button)

        button = QPushButton("Stop")
        button.setEnabled(False)
        self.voltmeter.active_changed.connect(button.setEnabled)
        button.clicked.connect(self.voltmeter.stop)
        layout.addWidget(button)

        # time
        label = QLabel("Time")
        sidebar_layout.addWidget(label)

        self.time_field = QLineEdit()
        self.time_field.setReadOnly(True)
        sidebar_layout.addWidget(self.time_field)

        # channels
        checkboxes = [BoolCheckBox(label) for label in self.labels]
        self.fields = [QLineEdit() for _ in self.labels]

        for (
            checkbox,
            field,
            channel,
        ) in zip(checkboxes, self.fields, self.channels, strict=True):
            checkbox.setChecked(True)
            sidebar_layout.addWidget(checkbox)
            checkbox.check_changed.connect(channel.setVisible)

            field.setReadOnly(True)
            sidebar_layout.addWidget(field)

        # save
        button = QPushButton("Save As")
        button.clicked.connect(self.on_save_as_clicked)
        sidebar_layout.addWidget(button)

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        sidebar_layout.addWidget(self.file_name)

        self.auto_save = BoolCheckBox("Automatic save")
        self.auto_save.setEnabled(False)
        self.auto_save.check_changed.connect(self.voltmeter.set_auto_save)
        # set_auto_save might cause a change back in case of an error
        self.voltmeter.auto_save_changed.connect(
            self.auto_save.setChecked, Qt.ConnectionType.QueuedConnection
        )
        sidebar_layout.addWidget(self.auto_save)

        button = QPushButton("Save Image")
        button.clicked.connect(self.on_save_image_clicked)
        sidebar_layout.addWidget(button)

        button = QPushButton("Reset")
        self.voltmeter.active_changed.connect(button.setDisabled)
        button.clicked.connect(self.on_reset_clicked)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        self.setLayout(window_layout)

    def get_upper_limit(self, value: float) -> float:
        for x in self.limits:
            if value <= x:
                return x

    @staticmethod
    def get_time_unit(time: float) -> float:
        if time <= 2.0 * 60.0:  # 2 minutes
            return 1  # seconds
        elif time <= 2 * 60.0 * 60.0:  # 2 hours
            return 60.0  # minutes
        else:
            return 60.0 * 60.0  # hours

    @staticmethod
    def get_unit_label(unit: float):
        if unit >= 60.0 * 60.0:
            return "time [hours]"
        elif unit >= 60.0:
            return "time [minutes]"
        else:
            return "time [seconds]"

    def get_batch_size(self, time: float) -> int:
        if time <= 2.0 * 60.0:  # 2 minutes
            return 1  # all points
        elif time <= 2 * 60.0 * 60.0:  # 2 hours
            return int(1000 / self.voltmeter.interval)  # seconds
        else:
            return int(1000 / self.voltmeter.interval) * 60  # minutes

    @Slot(VoltmeterPoint)
    def on_new_last_point(self, last_point: VoltmeterPoint):
        start = time.time()

        unit = self.get_time_unit(last_point.time)
        n = self.get_batch_size(last_point.time)

        # this can do 100_000 points in 400 ms not batched
        # and 130_000 points in 30 ms in batches of 50
        # a lot faster than channel.append
        for i, channel in enumerate(self.channels):
            channel.replace(
                [
                    QPointF(batch[0].time / unit, sum(point[i] for point in batch) / len(batch))
                    for batch in batched(self.voltmeter.points, n)
                ]
            )

        self.x_axis.setMax(self.get_upper_limit(last_point.time / unit))
        self.x_axis.setTitleText(self.get_unit_label(unit))
        self.time_field.setText(f"{last_point.time:g} s")
        for i, field in enumerate(self.fields):
            field.setText(f"{last_point[i]:.3f} V")

        logger.debug(
            f"on_new_last_point {len(self.voltmeter.points)} points"
            f"{int((time.time() - start) * 1000)} ms"
        )

    @Slot()
    def on_start_clicked(self):
        index = self.interval.currentIndex()
        interval = self.intervals[index]
        self.voltmeter.start(interval)

    def save_as(self) -> bool:
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, "Save", "voltmeter.csv", "CSV (*.csv)"
        )
        if not file_name:  # cancelled
            return False

        if self.voltmeter.save_as(file_name):
            self.file_name.setText(file_name)
            self.auto_save.setEnabled(True)
            return True

        return False

    @Slot()
    def on_save_as_clicked(self):
        self.save_as()

    @Slot()
    def on_reset_clicked(self):
        if self.voltmeter.unsaved:
            dialog = QMessageBox()
            dialog.setWindowTitle("Lenlab")
            dialog.setText("The voltmeter has unsaved data.")
            dialog.setInformativeText("Do you want to save the data?")
            dialog.setStandardButtons(
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )
            dialog.setDefaultButton(QMessageBox.StandardButton.Save)
            result = dialog.exec()
            if result == QMessageBox.StandardButton.Save:
                if not self.save_as():
                    return
            elif result == QMessageBox.StandardButton.Cancel:
                return

        self.voltmeter.reset()

        for channel in self.channels:
            channel.clear()
        self.unit = 1
        self.x_axis.setMax(4.0)
        self.x_axis.setTitleText(self.get_unit_label(self.unit))

        self.time_field.setText("")
        for field in self.fields:
            field.setText("")

        self.file_name.setText("")
        # self.auto_save.setChecked(False)  # changed signal
        self.auto_save.setEnabled(False)

    @Slot()
    def on_save_image_clicked(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self, "Save Image", "voltmeter.svg", "SVG (*.svg);;PNG (*.png)"
        )
        if not file_name:  # cancelled
            return

        try:
            fig, ax = plt.subplots()

            last_point = (
                self.voltmeter.points[-1]
                if self.voltmeter.points
                else VoltmeterPoint(4.0, 0.0, 0.0)
            )
            unit = self.get_time_unit(last_point.time)
            ax.set_xlim(0, self.get_upper_limit(last_point.time / unit))
            ax.set_ylim(0, 3.3)

            ax.set_xlabel(self.get_unit_label(unit))
            ax.set_ylabel("voltage [volts]")

            ax.grid()

            times = [point.time / unit for point in self.voltmeter.points]
            for i, channel in enumerate(self.channels):
                if channel.isVisible():
                    ax.plot(times, [point[i] for point in self.voltmeter.points])

            fig.savefig(file_name, format=file_format[:3].lower())
        except Exception as error:
            self.banner.set_error(VoltmeterSaveImageError(error))

    def closeEvent(self, event):
        if self.voltmeter.active or self.voltmeter.unsaved:
            dialog = QMessageBox()
            dialog.setWindowTitle("Lenlab")
            dialog.setText("The voltmeter is active or has unsaved data.")
            dialog.setInformativeText("Do you want to save the data?")
            dialog.setStandardButtons(
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )
            dialog.setDefaultButton(QMessageBox.StandardButton.Save)
            result = dialog.exec()
            if result == QMessageBox.StandardButton.Save:
                if not self.save_as():
                    event.ignore()
            elif result == QMessageBox.StandardButton.Cancel:
                event.ignore()

        if self.voltmeter.active and event.isAccepted():
            self.voltmeter.stop()
            self.voltmeter.save(0)


class VoltmeterSaveImageError(Message):
    english = """Error saving the image:\n\n{0}"""
    german = """Fehler beim Speichern des Bildes:\n\n{0}"""
