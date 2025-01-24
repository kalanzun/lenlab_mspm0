from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..launchpad import linux
from ..launchpad.discovery import Discovery, NoRules
from ..launchpad.terminal import LaunchpadError
from ..message import Message
from . import symbols


class PosterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.symbol_widget = QSvgWidget()
        # it does not recompute the size on loading
        # self.symbol_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.symbol_widget.setFixedSize(48, 48)

        self.text_widget = QLabel()
        self.text_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.text_widget.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_widget.setWordWrap(True)

        self.button = QPushButton()
        self.button.setHidden(True)

        right = QVBoxLayout()
        right.addWidget(self.text_widget)
        # AlignRight, short text, and the button could travel far away to the right
        right.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignLeft)

        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(self.symbol_widget, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(right, 1)

        self.setLayout(layout)

    def set_success(self, message: Message):
        self.symbol_widget.load(symbols.dye(symbols.check_box_48px, symbols.green))
        self.text_widget.setText("### " + message.long_form())

    def set_error(self, message: Message):
        self.symbol_widget.load(symbols.dye(symbols.error_48px, symbols.red))
        self.text_widget.setText("### " + message.long_form())


class StatusPoster(PosterWidget):
    retry = Signal()

    def __init__(self):
        super().__init__()

        self.rules = False
        self.button.clicked.connect(self.on_button_clicked)

    def attach(self, discovery: Discovery):
        discovery.ready.connect(self.hide)
        discovery.error.connect(self.on_error)

        self.retry.connect(discovery.retry)

    @Slot(Message)
    def on_error(self, error):
        if isinstance(error, LaunchpadError):
            self.symbol_widget.load(symbols.dye(symbols.usb_off_48px, symbols.red))
        else:
            self.symbol_widget.load(symbols.dye(symbols.developer_board_off_48px, symbols.red))

        self.text_widget.setText("### " + error.long_form())

        if isinstance(error, NoRules):
            self.rules = True
            self.button.setText("Install rules")
        else:
            self.rules = False
            self.button.setText("Retry")

        self.show()

    @Slot()
    def on_button_clicked(self):
        if self.rules:
            linux.install_rules()

        self.retry.emit()


class LaunchpadStatus(PosterWidget):
    def __init__(self):
        super().__init__()

        self.symbol_widget.setFixedSize(24, 24)
        self.text_widget.setWordWrap(False)

        self.no_launchpad()

    def attach(self, discovery: Discovery):
        discovery.available.connect(self.on_available)
        discovery.error.connect(self.on_error)

    def no_launchpad(self):
        self.symbol_widget.load(symbols.dye(symbols.usb_off_24px, symbols.red))
        self.text_widget.setText("No Launchpad")

    @Slot()
    def on_available(self):
        self.symbol_widget.load(symbols.dye(symbols.usb_24px, symbols.green))
        self.text_widget.setText("Launchpad ready")

    @Slot(Message)
    def on_error(self, error):
        if isinstance(error, LaunchpadError):
            self.no_launchpad()


class FirmwareStatus(LaunchpadStatus):
    def attach(self, discovery: Discovery):
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
