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

        self.button = QPushButton("Retry")
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

    def set_message(self, message: Message):
        self.text_widget.setText("### " + message.long_form())

    def set_symbol(self, symbol: bytes):
        self.symbol_widget.load(symbol)

    @Slot(Message)
    def set_success(self, message: Message):
        self.set_symbol(symbols.dye(symbols.check_box_48px, symbols.green))
        self.set_message(message)
        self.show()

    @Slot(Message)
    def set_error(self, message: Message):
        self.set_symbol(symbols.dye(symbols.error_48px, symbols.red))
        self.set_message(message)
        self.show()
