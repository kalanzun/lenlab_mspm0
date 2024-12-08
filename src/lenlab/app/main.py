from PySide6.QtCore import QLocale

from lenlab.app.app import App
from lenlab.app.window import MainWindow
from lenlab.message import Message


def main() -> int:
    app = App.get_instance()

    if QLocale().language() == QLocale.Language.German:
        Message.language = "german"

    window = MainWindow()
    window.show()

    return app.exec()
