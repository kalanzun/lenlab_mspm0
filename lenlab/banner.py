from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QPalette, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from . import symbols
from .messages import Category, Message


class MessageBanner(QWidget):
    def __init__(self):
        super().__init__()

        # self.setHidden(True)
        self.setAutoFillBackground(True)

        self.symbol_widget = QSvgWidget()
        self.symbol_widget.setFixedSize(40, 40)

        self.text_label = QLabel()
        self.help_label = QLabel()

        self.retry = QPushButton("Retry")

        body = QVBoxLayout()
        body.addWidget(self.text_label)
        body.addWidget(self.help_label)
        body.addWidget(self.retry, 0, Qt.AlignmentFlag.AlignRight)

        layout = QHBoxLayout()
        layout.addWidget(self.symbol_widget)
        layout.addLayout(body, 1)

        self.setLayout(layout)

    @Slot(Message)
    def set_message(self, message: Message):
        if message.category == Category.INFO:
            symbol = symbols.info
            palette = QPalette(QColor(0, 0x80, 0))
        elif message.category == Category.WARNING:
            symbol = symbols.warning
            palette = QPalette(QColor(0x80, 0x80, 0))
        else:
            symbol = symbols.error
            palette = QPalette(QColor(0x80, 0, 0))

        self.symbol_widget.load(symbol)
        self.setPalette(palette)

        text, *help = [line.strip() for line in message.get_text().splitlines()]
        self.text_label.setText(text)
        self.help_label.setText("\n".join(help))
        self.show()
