from PySide6.QtCore import Qt, Slot
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..device.device import Device
from ..device.lenlab import Lenlab
from ..launchpad.terminal import LaunchpadError, Terminal
from ..message import Message
from . import symbols


class StatusMessage(QWidget):
    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab

        self.symbol_widget = QSvgWidget()
        # it does not recompute the size on loading
        # self.symbol_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.symbol_widget.setFixedSize(48, 48)
        self.symbol_widget.load(symbols.dye(symbols.progress_activity_48px, symbols.yellow))

        self.text_widget = QLabel()
        self.text_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.text_widget.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_widget.setWordWrap(True)
        self.text_widget.setText("Connecting")

        self.button = QPushButton()
        self.button.clicked.connect(self.on_button_clicked)

        right = QVBoxLayout()
        right.addWidget(self.text_widget)
        # AlignRight, short text, and the button could travel far away to the right
        right.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft)

        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(self.symbol_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(right, 1)
        self.setLayout(layout)

        discovery = self.lenlab.discovery
        discovery.ready.connect(self.on_ready)
        discovery.error.connect(self.on_error)

    @Slot()
    def on_ready(self):
        self.hide()

    @Slot(Message)
    def on_error(self, error):
        if isinstance(error, LaunchpadError):
            self.symbol_widget.load(symbols.dye(symbols.usb_off_48px, symbols.red))
        else:
            self.symbol_widget.load(symbols.dye(symbols.developer_board_off_48px, symbols.red))

        self.text_widget.setText(f"### {error}")
        self.button.setText("Retry")
        self.show()

    @Slot()
    def on_button_clicked(self):
        pass


class StatusWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.symbol_widget = QSvgWidget()
        # it does not recompute the size on loading
        # self.symbol_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.symbol_widget.setFixedSize(24, 24)

        self.text_widget = QLabel()
        self.text_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.text_widget.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_widget.setWordWrap(False)

        self.no_launchpad()

        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(self.symbol_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.text_widget, 1)
        self.setLayout(layout)

    def no_launchpad(self):
        self.symbol_widget.load(symbols.dye(symbols.usb_off_24px, symbols.red))
        self.text_widget.setText("No Launchpad")


class LaunchpadStatus(StatusWidget):
    def __init__(self, device: Device):
        super().__init__()

        self.device = device

        lenlab = self.device.lenlab
        # lenlab.busy.connect(self.on_busy)

        discovery = lenlab.discovery
        discovery.available.connect(self.on_available)
        discovery.error.connect(self.on_error)

    @Slot()
    def on_available(self):
        self.symbol_widget.load(symbols.dye(symbols.usb_24px, symbols.green))
        self.text_widget.setText("Launchpad ready")

    @Slot(Message)
    def on_error(self, error):
        if isinstance(error, LaunchpadError):
            self.no_launchpad()


class FirmwareStatus(StatusWidget):
    def __init__(self, device: Device):
        super().__init__()

        self.device = device

        self.error_symbol = symbols.usb_off_24px
        self.error_message = "No Firmware"

        lenlab = self.device.lenlab
        # lenlab.busy.connect(self.on_busy)

        discovery = lenlab.discovery
        discovery.available.connect(self.on_available)
        discovery.ready.connect(self.on_ready)
        discovery.error.connect(self.on_error)

    def no_firmware(self):
        self.symbol_widget.load(symbols.dye(symbols.developer_board_off_24px, symbols.red))
        self.text_widget.setText("No Firmware")

    @Slot()
    def on_available(self):
        self.no_firmware()

    @Slot()
    def on_ready(self):
        self.symbol_widget.load(symbols.dye(symbols.developer_board_24px, symbols.green))
        self.text_widget.setText("Firmware ready")

    @Slot(Message)
    def on_error(self, error):
        if isinstance(error, LaunchpadError):
            self.no_launchpad()
        else:
            self.no_firmware()
