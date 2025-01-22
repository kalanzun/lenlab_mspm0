from importlib import metadata

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

from ..launchpad.discovery import Discovery
from ..launchpad.terminal import Terminal
from ..message import Message
from . import symbols


class BoardStatus(QWidget):
    def __init__(self, discovery: Discovery):
        super().__init__()

        self.discovery = discovery

        self.symbol_widget = QSvgWidget()
        # it does not recompute the size on loading
        # self.symbol_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.symbol_widget.setFixedSize(24, 24)
        self.symbol_widget.load(symbols.dye(symbols.progress_activity_24px, symbols.yellow))

        self.text_widget = QLabel()
        self.text_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.text_widget.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_widget.setText("Connecting")

        self.button = QPushButton()
        self.button.setHidden(True)
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

        self.discovery.ready.connect(self.on_ready)
        self.discovery.error.connect(self.on_error)

    @Slot()
    def on_button_clicked(self):
        pass

    @Slot(Terminal)
    def on_ready(self, terminal):
        self.symbol_widget.setFixedSize(24, 24)
        self.symbol_widget.load(symbols.dye(symbols.developer_board_24px, symbols.green))

        version = metadata.version("lenlab")
        self.text_widget.setText(f"Lenlab {version} connected and ready")
        self.text_widget.setWordWrap(False)

        self.button.hide()

    @Slot(Message)
    def on_error(self, error):
        self.symbol_widget.setFixedSize(48, 48)
        self.symbol_widget.load(symbols.dye(symbols.developer_board_off_48px, symbols.red))

        self.text_widget.setText(f"### {error}")
        self.text_widget.setWordWrap(True)

        self.button.setText("Retry")
        self.button.show()
