from lenlab.app.window import MainWindow
from lenlab.message import Message


def test_main_window():
    MainWindow()


def test_main_window_german():
    Message.language = "german"

    MainWindow()
