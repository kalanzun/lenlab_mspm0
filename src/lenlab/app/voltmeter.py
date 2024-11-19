from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QIODevice, QSaveFile, Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QCheckBox,
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

from ..model.lenlab import Lenlab
from ..model.voltmeter import Voltmeter


class VoltmeterWidget(QWidget):
    title = "Voltmeter"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab
        self.voltmeter = Voltmeter()
        self.lenlab.ready.connect(self.voltmeter.set_terminal)
        self.voltmeter.new_point.connect(self.on_new_point)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.ch1 = QLineSeries()
        self.ch1.setName("Channel 1")
        self.ch2 = QLineSeries()
        self.ch2.setName("Channel 2")
        self.unit = 1  # second

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart = self.chart_view.chart()
        chart.setTheme(QChart.ChartTheme.ChartThemeDark)

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

        for channel in (self.ch1, self.ch2):
            chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(self.y_axis)

        main_layout.addWidget(self.chart_view, stretch=1)

        sidebar_layout = QVBoxLayout()
        main_layout.addLayout(sidebar_layout)

        # sample rate
        layout = QHBoxLayout()
        sidebar_layout.addLayout(layout)

        label = QLabel("Sample rate")
        layout.addWidget(label)

        self.sample_rate = QComboBox()
        layout.addWidget(self.sample_rate)

        self.sample_rate.addItem("200ms")
        self.sample_rate.addItem("500ms")
        self.sample_rate.addItem("1s")
        self.sample_rate.addItem("2s")

        self.sample_rate.setCurrentIndex(2)

        # start / stop
        layout = QHBoxLayout()
        sidebar_layout.addLayout(layout)

        button = QPushButton("Start")
        button.clicked.connect(self.voltmeter.start)
        layout.addWidget(button)

        button = QPushButton("Stop")
        button.clicked.connect(self.voltmeter.stop)
        layout.addWidget(button)

        # channels
        checkbox = QCheckBox("Channel 1 (PA 24)")
        checkbox.setChecked(True)
        checkbox.checkStateChanged.connect(
            lambda state: self.ch1.setVisible(state == Qt.CheckState.Checked)
        )
        sidebar_layout.addWidget(checkbox)

        checkbox = QCheckBox("Channel 2 (PA 17)")
        checkbox.setChecked(True)
        checkbox.checkStateChanged.connect(
            lambda state: self.ch2.setVisible(state == Qt.CheckState.Checked)
        )
        sidebar_layout.addWidget(checkbox)

        # save
        button = QPushButton("Save")
        button.clicked.connect(self.save)
        sidebar_layout.addWidget(button)

        self.auto_save = QCheckBox("Automatic save")
        sidebar_layout.addWidget(self.auto_save)

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        sidebar_layout.addWidget(self.file_name)

        button = QPushButton("Reset")
        button.clicked.connect(self.voltmeter.reset)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

    limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0, 200.0]

    def get_upper_limit(self, value: float) -> float:
        for x in self.limits:
            if x > value:
                return x

    @staticmethod
    def get_time_unit(time: float) -> float:
        if time < 2.0 * 60.0:  # 2 minutes
            return 1  # seconds
        elif time < 2 * 60.0 * 60.0:  # 2 hours
            return 60.0  # minutes
        else:
            return 60.0 * 60.0  # hours

    @Slot(float, float, float)
    def on_new_point(self, time, value1, value2):
        unit = self.get_time_unit(time)
        if unit != self.unit:
            self.ch1.clear()
            self.ch2.clear()
            self.unit = unit
            for time, value1, value2 in self.voltmeter.points:
                self.ch1.append((time / unit), value1)
                self.ch2.append((time / unit), value2)

            if unit >= 60.0 * 60.0:
                self.x_axis.setTitleText("time [hours]")
            elif unit >= 60.0:
                self.x_axis.setTitleText("time [minutes]")
            else:
                self.x_axis.setTitleText("time [seconds]")

        else:
            self.ch1.append(time / unit, value1)
            self.ch2.append(time / unit, value2)

        self.x_axis.setMax(self.get_upper_limit(time / unit))

    @Slot()
    def on_reset(self):
        self.voltmeter.reset()
        self.ch1.clear()
        self.ch2.clear()
        self.unit = 1
        self.x_axis.setMax(4.0)
        self.x_axis.setTitleText("time [seconds]")

    @Slot()
    def save(self):
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, "Save", "voltmeter.csv", "CSV (*.csv)"
        )
        if not file_name:  # cancelled
            return

        file = QSaveFile(file_name)

        if not file.open(QIODevice.OpenModeFlag.WriteOnly):
            QMessageBox.critical(
                self, "Save", f"Fehler beim Speichern der Daten\n{file.errorString()}"
            )
            return

        file.write(b"Hello!\n")

        if not file.commit():
            QMessageBox.critical(
                self, "Save", f"Fehler beim Speichern der Daten\n{file.errorString()}"
            )
            return

        self.auto_save.setChecked(False)
        self.file_name.setText(file_name)
