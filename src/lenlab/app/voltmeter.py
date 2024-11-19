from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, Signal, Slot
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
from ..model.voltmeter import Voltmeter
from .checkbox import BoolCheckBox


class VoltmeterWidget(QWidget):
    title = "Voltmeter"

    labels = ("Channel 1 (PA 24)", "Channel 2 (PA 17)")
    limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0]
    intervals = [20, 50, 100, 200, 500, 1000]

    error = Signal(Message)

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab
        self.voltmeter = Voltmeter()
        self.lenlab.ready.connect(self.voltmeter.set_terminal)
        self.voltmeter.new_records.connect(self.on_new_records)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.channels = [QLineSeries() for _ in self.labels]
        for channel, label in zip(self.channels, self.labels, strict=False):
            channel.setName(label)
        self.unit = 1  # second

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart = self.chart_view.chart()
        # chart.setTheme(QChart.ChartTheme.ChartThemeLight)  # default, grid lines faint
        # chart.setTheme(QChart.ChartTheme.ChartThemeDark)  # odd gradient
        # chart.setTheme(QChart.ChartTheme.ChartThemeBlueNcs)  # grid lines faint
        chart.setTheme(QChart.ChartTheme.ChartThemeQt)  # light and dark green, stronger grid lines

        self.x_axis = QValueAxis()
        self.x_axis.setRange(0.0, 4.0)
        self.x_axis.setTickCount(5)
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText("time [seconds]")
        chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(0.0, 3.3)
        self.y_axis.setTickCount(5)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText("voltage [volts]")
        chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        for channel in self.channels:
            chart.addSeries(channel)
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
        self.voltmeter.started_changed.connect(self.interval.setDisabled)
        layout.addWidget(self.interval)

        for interval in self.intervals:
            self.interval.addItem(f"{interval} ms")
        self.interval.setCurrentIndex(len(self.intervals) - 1)

        # start / stop
        layout = QHBoxLayout()
        sidebar_layout.addLayout(layout)

        button = QPushButton("Start")
        self.voltmeter.started_changed.connect(button.setDisabled)
        button.clicked.connect(self.on_start_clicked)
        layout.addWidget(button)

        button = QPushButton("Stop")
        button.setEnabled(False)
        self.voltmeter.started_changed.connect(button.setEnabled)
        button.clicked.connect(self.voltmeter.stop)
        layout.addWidget(button)

        # time
        label = QLabel("Time")
        sidebar_layout.addWidget(label)

        self.time_field = QLineEdit()
        self.time_field.setReadOnly(True)
        sidebar_layout.addWidget(self.time_field)

        # channels
        self.fields = [QLineEdit() for _ in self.labels]

        for channel, field, label in zip(self.channels, self.fields, self.labels, strict=False):
            checkbox = BoolCheckBox(label)
            checkbox.setChecked(True)
            checkbox.check_changed.connect(channel.setVisible)
            sidebar_layout.addWidget(checkbox)

            field.setReadOnly(True)
            sidebar_layout.addWidget(field)

        # save
        button = QPushButton("Save")
        button.clicked.connect(self.on_save_clicked)
        sidebar_layout.addWidget(button)

        self.auto_save = BoolCheckBox("Automatic save")
        self.auto_save.setEnabled(False)
        self.auto_save.check_changed.connect(self.voltmeter.set_auto_save)
        sidebar_layout.addWidget(self.auto_save)

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        sidebar_layout.addWidget(self.file_name)

        button = QPushButton("Reset")
        self.voltmeter.started_changed.connect(button.setDisabled)
        button.clicked.connect(self.on_reset_clicked)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

    @Slot()
    def on_start_clicked(self):
        index = self.interval.currentIndex()
        interval = self.intervals[index]
        self.voltmeter.start(interval)

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

    @Slot(list)
    def on_new_records(self, new_records: list[tuple[float, float, float]]):
        unit = self.get_time_unit(new_records[-1][0])
        if unit != self.unit:
            for channel in self.channels:
                channel.clear()
            self.unit = unit
            for time, *values in self.voltmeter.records:
                for channel, value in zip(self.channels, values, strict=False):
                    channel.append((time / unit), value)

            if unit >= 60.0 * 60.0:
                self.x_axis.setTitleText("time [hours]")
            elif unit >= 60.0:
                self.x_axis.setTitleText("time [minutes]")
            else:
                self.x_axis.setTitleText("time [seconds]")

        else:
            for time, *values in new_records:
                for channel, value in zip(self.channels, values, strict=False):
                    channel.append((time / unit), value)

        time, *values = new_records[-1]
        self.x_axis.setMax(self.get_upper_limit(time / unit))

        self.time_field.setText(f"{time:g} s")
        for field, value in zip(self.fields, values, strict=False):
            field.setText(f"{value:.3f} V")

    def save(self) -> bool:
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, "Save", "voltmeter.csv", "CSV (*.csv)"
        )
        if not file_name:  # cancelled
            return False

        self.voltmeter.set_file_name(file_name)
        if self.voltmeter.save():
            self.file_name.setText(file_name)
            self.auto_save.setChecked(False)
            self.auto_save.setEnabled(True)
        else:
            self.file_name.setText("")
            self.auto_save.setChecked(False)
            self.auto_save.setEnabled(False)
            return False

        return True

    @Slot()
    def on_save_clicked(self):
        self.save()

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
                if not self.save():
                    return
            elif result == QMessageBox.StandardButton.Cancel:
                return

        self.voltmeter.reset()

        for channel in self.channels:
            channel.clear()
        self.unit = 1
        self.x_axis.setMax(4.0)
        self.x_axis.setTitleText("time [seconds]")

        self.time_field.setText("")
        for field in self.fields:
            field.setText("")

        self.file_name.setText("")
        self.auto_save.setChecked(False)
        self.auto_save.setEnabled(False)
