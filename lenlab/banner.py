from PySide6.QtCore import Slot, QLocale
from PySide6.QtGui import QColor, QPalette, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from . import symbols
from .messages import Category, Message


class MessageBanner(QWidget):
    palette_by_category = {
        Category.ERROR: QPalette(QColor(0x80, 0, 0)),
        Category.WARNING: QPalette(QColor(0x80, 0x80, 0)),
        Category.INFO: QPalette(QColor(0, 0x80, 0)),
    }

    symbol_by_category = {
        Category.ERROR: symbols.error,
        Category.WARNING: symbols.warning,
        Category.INFO: symbols.info,
    }

    def __init__(self):
        super().__init__()

        # self.setHidden(True)
        self.setAutoFillBackground(True)

        self.symbol_widget = QSvgWidget()
        self.symbol_widget.setFixedSize(40, 40)

        self.text_label = QLabel()
        self.retry_button = QPushButton("Retry")

        body = QVBoxLayout()
        body.addWidget(self.text_label)
        body.addWidget(self.retry_button, 0, Qt.AlignmentFlag.AlignRight)

        layout = QHBoxLayout()
        layout.addWidget(self.symbol_widget)
        layout.addLayout(body, 1)

        self.setLayout(layout)

    @Slot(Message)
    def set_message(self, message: Message):
        self.setPalette(self.palette_by_category[message.category])
        self.symbol_widget.load(self.symbol_by_category[message.category])
        self.text_label.setText(message.get_text(QLocale().language()))
        self.retry_button.setHidden(message.category == Category.INFO)
        self.show()
