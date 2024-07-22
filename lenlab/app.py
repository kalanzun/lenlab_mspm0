import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from .message import Message
from .window import MainWindow


def main():
    app = QApplication(sys.argv)

    if QLocale().language() == QLocale.Language.German:
        Message.language = "german"

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
