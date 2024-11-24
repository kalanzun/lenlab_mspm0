import logging
import time
from datetime import timedelta
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
from .dialog import Dialog
from .vocabulary import Vocabulary as Vocab

logger = logging.getLogger(__name__)


class VoltmeterChart(QWidget):
    labels = (
        Vocab("Channel 1 (PA 24)", "Kanal 1 (PA 24)"),
        Vocab("Channel 2 (PA 17)", "Kanal 2 (PA 17)"),
    )
    limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0]

    x_label = Vocab.time
    y_label = Vocab.voltage

    amplitude_label = Vocab.volt
    time_labels = {
        1: Vocab.seconds,
        60: Vocab.minutes,
        60 * 60: Vocab.hours,
    }

    def get_limit(self, value: float) -> float:
        for x in self.limits:
            if x >= value:
                return x

    def get_x_label(self, unit: int) -> str:
        return f"{self.x_label} [{self.time_labels[unit]}]"

    def get_y_label(self) -> str:
        return f"{self.y_label} [{self.amplitude_label}]"

    def __init__(self, voltmeter: Voltmeter):
        super().__init__()

        self.voltmeter = voltmeter
        self.voltmeter.new_last_point.connect(
            self.on_new_last_point, Qt.ConnectionType.QueuedConnection
        )

        self.unit = 1  # second

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
        self.x_axis.setTitleText(self.get_x_label(self.unit))
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(0.0, 3.3)
        self.y_axis.setTickCount(5)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText(self.get_y_label())
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
    def get_time_unit(value: float) -> int:
        if value <= 2.0 * 60.0:  # 2 minutes
            return 1  # seconds
        elif value <= 2 * 60.0 * 60.0:  # 2 hours
            return 60  # minutes
        else:
            return 60 * 60  # hours

    @staticmethod
    def get_batch_size(last_time: float, interval: int) -> int:
        if last_time <= 2.0 * 60.0:  # 2 minutes
            return 1  # all points
        elif last_time <= 2 * 60.0 * 60.0:  # 2 hours
            return 1000 // interval  # seconds
        else:
            return 1000 // interval * 60  # minutes

    @Slot(VoltmeterPoint)
    def on_new_last_point(self, last_point: VoltmeterPoint):
        start = time.time()

        unit = self.get_time_unit(last_point.time)
        n = self.get_batch_size(last_point.time, self.voltmeter.interval)

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

        self.x_axis.setMax(self.get_limit(last_point.time / unit))
        self.x_axis.setTitleText(self.get_x_label(unit))

        logger.debug(
            f"on_new_last_point {len(self.voltmeter.points)} points"
            f"{int((time.time() - start) * 1000)} ms"
        )

    def discard(self):
        for channel in self.channels:
            channel.clear()
        self.unit = 1
        self.x_axis.setMax(4.0)
        self.x_axis.setTitleText(self.get_x_label(self.unit))

    def save_image(self, file_name, file_format):
        fig, ax = plt.subplots()

        last_point = (
            self.voltmeter.points[-1] if self.voltmeter.points else VoltmeterPoint(4.0, 0.0, 0.0)
        )
        unit = self.get_time_unit(last_point.time)
        ax.set_xlim(0, self.get_limit(last_point.time / unit))
        ax.set_ylim(0, 3.3)

        ax.set_xlabel(self.get_x_label(unit))
        ax.set_ylabel(self.get_y_label())

        ax.grid()

        times = [point.time / unit for point in self.voltmeter.points]
        for i, channel in enumerate(self.channels):
            if channel.isVisible():
                ax.plot(times, [point[i] for point in self.voltmeter.points])

        fig.savefig(file_name, format=file_format[:3].lower())


class VoltmeterWidget(QWidget):
    title = Vocab("Voltmeter", "Voltmeter")
    intervals = [20, 50, 100, 200, 500, 1000]

    interval: QComboBox
    time_field: QLineEdit
    fields: list[QLineEdit]
    file_name: QLineEdit
    auto_save: BoolCheckBox

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab
        self.voltmeter = Voltmeter(lenlab)
        self.voltmeter.new_last_point.connect(
            self.on_new_last_point, Qt.ConnectionType.QueuedConnection
        )

        self.unit = 1  # second

        self.banner = MessageBanner(button_text=Vocab.hide)
        self.banner.button.clicked.connect(self.banner.hide)
        self.voltmeter.error.connect(self.banner.set_error)

        self.chart = VoltmeterChart(self.voltmeter)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.chart, stretch=1)
        main_layout.addLayout(self.create_sidebar())

        window_layout = QVBoxLayout()
        window_layout.addWidget(self.banner)
        window_layout.addLayout(main_layout)

        self.setLayout(window_layout)

    def create_sidebar(self):
        sidebar_layout = QVBoxLayout()

        # interval
        self.interval = QComboBox()
        for interval in self.intervals:
            self.interval.addItem(f"{interval} ms")
        self.interval.setCurrentIndex(len(self.intervals) - 1)
        self.voltmeter.active_changed.connect(self.interval.setDisabled)

        layout = QHBoxLayout()

        label = QLabel(str(Vocab.interval))
        layout.addWidget(label)
        layout.addWidget(self.interval)

        sidebar_layout.addLayout(layout)

        # start / stop
        layout = QHBoxLayout()

        button = QPushButton(str(Vocab.start))
        self.voltmeter.active_changed.connect(button.setDisabled)
        button.clicked.connect(self.on_start_clicked)
        layout.addWidget(button)

        button = QPushButton(str(Vocab.stop))
        button.setEnabled(False)
        self.voltmeter.active_changed.connect(button.setEnabled)
        button.clicked.connect(self.voltmeter.stop)
        layout.addWidget(button)

        sidebar_layout.addLayout(layout)

        # time
        label = QLabel(str(Vocab.time))
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

        # save
        button = QPushButton(str(Vocab.save_as))
        button.clicked.connect(self.on_save_as_clicked)
        sidebar_layout.addWidget(button)

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        sidebar_layout.addWidget(self.file_name)

        self.auto_save = BoolCheckBox(Vocab.automatic_save)
        self.auto_save.setEnabled(False)
        self.auto_save.check_changed.connect(self.voltmeter.set_auto_save)
        # set_auto_save might cause a change back in case of an error
        self.voltmeter.auto_save_changed.connect(
            self.auto_save.setChecked, Qt.ConnectionType.QueuedConnection
        )
        sidebar_layout.addWidget(self.auto_save)

        button = QPushButton(str(Vocab.save_image))
        button.clicked.connect(self.on_save_image_clicked)
        sidebar_layout.addWidget(button)

        button = QPushButton(str(Vocab.discard))
        self.voltmeter.active_changed.connect(button.setDisabled)
        button.clicked.connect(self.on_discard_clicked)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        return sidebar_layout

    @Slot(VoltmeterPoint)
    def on_new_last_point(self, last_point: VoltmeterPoint):
        seconds = timedelta(seconds=int(last_point.time))
        if fractional := last_point.time % 1.0 or self.voltmeter.interval < 1000:  # ms
            milliseconds = f"{fractional:.2f}"[1:]
            self.time_field.setText(f"{seconds}{milliseconds}")
        else:
            self.time_field.setText(str(seconds))

        for i, field in enumerate(self.fields):
            field.setText(f"{last_point[i]:.3f} V")

    @Slot()
    def on_start_clicked(self):
        index = self.interval.currentIndex()
        interval = self.intervals[index]
        self.voltmeter.start(interval)

    def save_as(self) -> bool:
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, str(Vocab.save_as), "voltmeter.csv", "CSV (*.csv)"
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
    def on_discard_clicked(self):
        if self.voltmeter.unsaved:
            dialog = SaveQuestion()
            dialog.setStandardButtons(
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )
            result = dialog.exec()
            if result == QMessageBox.StandardButton.Save:
                if not self.save_as():
                    return
            elif result == QMessageBox.StandardButton.Cancel:
                return

        self.voltmeter.discard()
        self.chart.discard()

        self.time_field.setText("")
        for field in self.fields:
            field.setText("")

        self.file_name.setText("")
        # self.auto_save.setChecked(False)  # changed signal
        self.auto_save.setEnabled(False)

    @Slot()
    def on_save_image_clicked(self):
        file_name, file_format = QFileDialog.getSaveFileName(
            self, str(Vocab.save_image), "voltmeter.svg", "SVG (*.svg);;PNG (*.png)"
        )
        if not file_name:  # cancelled
            return

        try:
            self.chart.save_image(file_name, file_format)
        except Exception as error:
            self.banner.set_error(SaveImageError(error))

    def closeEvent(self, event):
        if self.voltmeter.active or self.voltmeter.unsaved:
            dialog = SaveQuestion()
            dialog.setStandardButtons(
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            )
            result = dialog.exec()
            if result == QMessageBox.StandardButton.Save:
                if not self.save_as():
                    event.ignore()
            elif result == QMessageBox.StandardButton.Cancel:
                event.ignore()

        if self.voltmeter.active and event.isAccepted():
            self.voltmeter.stop()
            self.voltmeter.save(0)


class SaveImageError(Message):
    english = """Error saving the image:\n\n{0}"""
    german = """Fehler beim Speichern des Bildes:\n\n{0}"""


class SaveQuestion(Dialog):
    text = Vocab("The voltmeter has unsaved data.", "Das Voltmeter hat ungespeicherte Daten.")
    info = Vocab("Do you want to save the data?", "Möchten Sie die Daten speichern?")
