from PySide6.QtCharts import QChartView
from PySide6.QtCore import QIODevice, QSaveFile, Slot
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


class Voltmeter(QWidget):
    title = "Voltmeter"

    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        layout.addWidget(button)

        button = QPushButton("Stop")
        layout.addWidget(button)

        # channels
        checkbox = QCheckBox("Channel 1")
        sidebar_layout.addWidget(checkbox)

        checkbox = QCheckBox("Channel 2")
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
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

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
