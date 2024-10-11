from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Voltmeter(QWidget):
    title = "Voltmeter"
    description = "Voltage measurement and logging"

    def __init__(self):
        super().__init__()

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        main_layout.addWidget(self.chart_view)

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
        layout.addWidget(button)

        button = QPushButton("Stop")
        layout.addWidget(button)

        # channels
        checkbox = QCheckBox("Channel 1")
        sidebar_layout.addWidget(checkbox)

        checkbox = QCheckBox("Channel 2")
        sidebar_layout.addWidget(checkbox)
