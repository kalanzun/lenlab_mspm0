import logging
from datetime import timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..controller.auto_save import AutoSave, Flag
from ..controller.image import save_image
from ..controller.lenlab import Lenlab
from ..launchpad.protocol import command
from ..message import Message
from ..model.chart import Chart
from ..model.points import Points
from ..translate import Translate, tr
from .chart import ChartWidget
from .checkbox import BoolCheckBox
from .save_as import SaveAs, UnsavedData

logger = logging.getLogger(__name__)


class VoltmeterWidget(QWidget):
    title = Translate("Voltmeter", "Voltmeter")

    # TODO convert to seconds
    intervals = [20, 50, 100, 200, 500, 1000, 2000]

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab

        self.started = Flag()
        self.polling = Flag()

        self.auto_save = AutoSave()

        # poll interval
        self.poll_timer = QTimer()
        self.poll_timer.setSingleShot(True)
        self.poll_timer.timeout.connect(self.on_poll_timeout)

        chart_layout = QVBoxLayout()

        self.chart = ChartWidget(Chart())
        chart_layout.addWidget(self.chart, 1)

        sidebar_layout = QVBoxLayout()

        # interval
        self.interval = QComboBox()
        for interval in self.intervals:
            self.interval.addItem(f"{interval} ms")
        self.interval.setCurrentIndex(self.intervals.index(200))

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
        self.started.changed.connect(button.setEnabled)
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
        self.auto_save.file_path.changed.connect(self.file_name.setText)
        sidebar_layout.addWidget(self.file_name)

        checkbox = BoolCheckBox(tr("Automatic saving", "Automatisch speichern"))
        # self.auto_save_check_box.setEnabled(False)
        checkbox.check_changed.connect(self.auto_save.auto_save.set)
        # auto_save.set might cause a change back in case of an error
        self.auto_save.auto_save.changed.connect(
            checkbox.setChecked, Qt.ConnectionType.QueuedConnection
        )
        sidebar_layout.addWidget(checkbox)

        button = QPushButton(tr("Save image", "Bild speichern"))
        button.clicked.connect(self.on_save_image_clicked)
        sidebar_layout.addWidget(button)

        button = QPushButton(tr("Discard", "Verwerfen"))
        self.started.changed.connect(button.setDisabled)
        button.clicked.connect(self.on_discard_clicked)
        sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(chart_layout, stretch=1)
        main_layout.addLayout(sidebar_layout)

        self.setLayout(main_layout)

        self.lenlab.ready.connect(self.on_ready)
        self.lenlab.reply.connect(self.on_reply)

    def clear(self):
        if not self.auto_save.points.index:
            return

        self.auto_save.clear()
        self.chart.clear()
        self.interval.setEnabled(True)
        self.time_field.setText("")
        for field in self.fields:
            field.setText("")

    @staticmethod
    def format_time(time: float, show_ms: bool = True) -> str:
        td = timedelta(seconds=time)
        if td.microseconds:
            return str(td)[:-4]
        elif show_ms:
            return f"{td}.00"
        else:
            return str(td)

    def draw(self, points: Points):
        self.auto_save.save_update(buffered=True)
        if points.chart_updated:
            self.chart.draw(points.create_chart())

        self.time_field.setText(self.format_time(points.get_last_time(), points.interval < 1.0))
        for i, field in enumerate(self.fields):
            if field.isEnabled():
                field.setText(f"{points.get_last_value(i):.3f} V")

    @Slot(bool)
    def on_ready(self, ready: bool):
        self.started.set(False)
        self.polling.set(False)

    @Slot()
    def on_start_clicked(self):
        if self.started or self.polling:
            return

        if self.lenlab.adc_lock.acquire():
            index = self.interval.currentIndex()
            interval_25ns = self.intervals[index] * 40_000
            self.started.set(True)
            self.polling.set(True)
            logger.debug("send start command")
            self.lenlab.send_command(command(b"v", interval_25ns))

    @Slot()
    def on_stop_clicked(self):
        if not self.polling:
            return

        self.polling.set(False)
        self.poll_timer.setInterval(0)  # timeout immediately

    @Slot()
    def on_poll_timeout(self):
        if not self.polling:
            logger.debug("send stop command")

        self.lenlab.send_command(command(b"x", int(bool(self.polling))))

    @Slot(bytes)
    def on_reply(self, reply):
        points = self.auto_save.points

        if reply.startswith(b"Lv"):  # start
            interval_25ns = int.from_bytes(reply[4:8], byteorder="little")
            interval = interval_25ns / 40_000_000

            points.interval = interval
            self.interval.setEnabled(False)

            if self.polling:  # no very quick stop pending
                interval_ms = max(200, interval_25ns // 40_000)
                self.poll_timer.setInterval(interval_ms)

            logger.debug("started")
            self.poll_timer.start()

        elif reply.startswith(b"Lx"):  # new points
            length = int.from_bytes(reply[2:4], byteorder="little")
            polling = int.from_bytes(reply[4:8], byteorder="little")

            if length:
                points.parse_reply(reply)
                self.draw(points)

            if polling:  # continue
                self.poll_timer.start()
            else:  # stop
                self.lenlab.adc_lock.release()
                self.started.set(False)
                self.auto_save.save_update(buffered=False)
                logger.debug("stopped")

    def create_save_as_dialog(self) -> SaveAs:
        dialog = SaveAs(self)
        dialog.setWindowTitle(tr("Save voltmeter data", "Voltmeter-Daten speichern"))
        dialog.set_default_file_name("lenlab_volt.csv")
        return dialog

    def create_unsaved_data_dialog(self) -> UnsavedData:
        dialog = UnsavedData(self)
        dialog.setWindowTitle(tr("Unsaved voltmeter data", "Ungespeicherte Voltmeter-Daten"))
        if self.started:
            dialog.setText(RunningAndUnsavedMessage().long_form())
        else:
            dialog.setText(UnsavedMessage().long_form())

        return dialog

    @Slot()
    def on_save_as_clicked(self):
        dialog = self.create_save_as_dialog()
        dialog.on_save_as = self.auto_save.save_as
        dialog.open()

    @Slot()
    def on_save_image_clicked(self):
        dialog = SaveAs(self)
        dialog.setWindowTitle(tr("Save voltmeter image", "Voltmeter-Bild speichern"))
        dialog.set_default_file_name("lenlab_volt.svg")
        dialog.on_save_as = self.on_save_image
        dialog.open()

    def on_save_image(self, file_path: Path):
        chart = self.auto_save.points.create_chart()
        channel_enabled = [channel.isVisible() for channel in self.chart.channels]
        save_image(file_path, chart, channel_enabled)

    @Slot()
    def on_discard_clicked(self):
        if self.started:
            return

        if self.auto_save.points.unsaved:
            dialog = self.create_unsaved_data_dialog()
            dialog.on_save = self.on_save_as_and_discard
            dialog.on_discard = self.clear
            dialog.open()
        else:
            self.clear()

    def on_save_as_and_discard(self):
        dialog = self.create_save_as_dialog()
        dialog.on_save_as = self.auto_save.save_as
        dialog.on_success = self.clear
        dialog.open()

    def on_close_event(self, event: QCloseEvent):
        if self.polling or self.auto_save.points.unsaved:
            event.ignore()

            dialog = self.create_unsaved_data_dialog()
            dialog.on_save = self.on_save_as_and_close
            dialog.on_discard = self.on_discard_and_close
            dialog.open()

    def on_discard_and_close(self):
        self.on_stop_clicked()

        self.auto_save.points.unsaved = False
        self.lenlab.close.emit()

    def on_save_as_and_close(self):
        self.on_stop_clicked()

        dialog = self.create_save_as_dialog()
        dialog.on_save_as = self.auto_save.save_as
        dialog.on_success = self.lenlab.close.emit
        dialog.open()


class RunningAndUnsavedMessage(Message):
    english = """The voltmeter is still running or has unsaved data.
    Do you want to stop the measurement and save the data?"""

    german = """Das Voltmeter läuft noch oder hat ungespeicherte Daten.
    Möchten Sie die Messung beenden und die Daten speichern?"""


class UnsavedMessage(Message):
    english = """The voltmeter has unsaved data.
    Do you want to save the data?"""

    german = """Das Voltmeter hat ungespeicherte Daten.
    Möchten Sie die Daten speichern?"""
