from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QPalette, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..message import Message
from . import symbols


class MessageBanner(QWidget):
    def __init__(self, button_text=None):
        super().__init__()

        self.hide()
        self.setAutoFillBackground(True)

        self.symbol_widget = QSvgWidget()
        self.symbol_widget.setFixedSize(40, 40)

        self.text_label = QLabel()

        body = QVBoxLayout()
        body.addWidget(self.text_label)
        if button_text:
            self.button = QPushButton(str(button_text))
            body.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignRight)

        layout = QHBoxLayout()
        layout.addWidget(self.symbol_widget)
        layout.addLayout(body)

        self.setLayout(layout)

    @Slot(Message)
    def set_success(self, message: Message):
        self.setPalette(QPalette(QColor(0, 0x80, 0)))
        self.symbol_widget.load(symbols.info)
        self.text_label.setText(str(message))
        self.show()

    @Slot(Message)
    def set_warning(self, message: Message):
        self.setPalette(QPalette(QColor(0x80, 0x80, 0)))
        self.symbol_widget.load(symbols.warning)
        self.text_label.setText(str(message))
        self.show()

    @Slot(Message)
    def set_error(self, message: Message):
        self.setPalette(QPalette(QColor(0x80, 0, 0)))
        self.symbol_widget.load(symbols.error)
        self.text_label.setText(str(message))
        self.show()
