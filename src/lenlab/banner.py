from PySide6.QtGui import QColor, QPalette, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from . import symbols


class MessageBanner(QWidget):
    def __init__(self):
        super().__init__()

        # self.setHidden(True)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.symbol_widget = QSvgWidget()
        layout.addWidget(self.symbol_widget)

        self.symbol_widget.setFixedSize(40, 40)

        body = QVBoxLayout()
        layout.addLayout(body, 1)

        self.text = QLabel()
        body.addWidget(self.text)

        self.button = QPushButton()
        body.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)

    def set_message(self, message: str, color: QColor, symbol: bytes, button: str = ""):
        self.text.setText(str(message))
        self.setPalette(QPalette(color))
        self.symbol_widget.load(symbol)
        if button:
            self.button.setHidden(False)
            self.button.setText(button)
        else:
            self.button.setHidden(True)

        self.show()

    def set_info(self, message: str, button: str = ""):
        self.set_message(message, QColor(0, 0x80, 0), symbols.info, button)

    def set_warning(self, message: str, button: str = ""):
        self.set_message(message, QColor(0x80, 0x80, 0), symbols.warning, button)

    def set_error(self, message: str, button: str = ""):
        self.set_message(message, QColor(0x80, 0, 0), symbols.error, button)
