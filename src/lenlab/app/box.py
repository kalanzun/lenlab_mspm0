from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..message import Message
from . import symbols


class Box(QWidget):
    def __init__(self):
        super().__init__()

        self.symbol_widget = QSvgWidget()
        self.symbol_widget.setFixedSize(40, 40)

        self.text_widget = QLabel()
        self.text_widget.setTextFormat(Qt.TextFormat.MarkdownText)
        self.text_widget.setWordWrap(True)

        self.button = QPushButton()
        self.error = None
        self.button.clicked.connect(self.on_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.symbol_widget)
        layout.addWidget(self.text_widget)

        main = QVBoxLayout()
        main.addLayout(layout)
        main.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(main)

        self.hide()

    @staticmethod
    def paint(painter: QPainter):
        width, height = painter.device().width(), painter.device().height()
        padding = 2
        roundness = 2

        # alpha < 255 -> a little darker in dark mode, lighter in light mode
        painter.setBrush(QColor(0xFF, 0, 0, 0xC0))
        painter.setPen(QColor(0xFF, 0, 0))
        painter.drawRoundedRect(
            padding,
            padding,
            width - 2 * padding,
            height - 2 * padding,
            roundness,
            roundness,
        )

    def paintEvent(self, event):  # pragma: no cover
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.paint(painter)

    def on_clicked(self):
        self.hide()
        if self.error is not None and self.error.callback is not None:
            self.error.callback()

    def set_error(self, error: Message):
        self.error = error
        self.symbol_widget.load(symbols.error)
        self.text_widget.setText(str(error))
        self.button.setText(str(error.button))
        self.show()
