from lenlab.app.window import MainWindow
from lenlab.message import Message


def test_main_window(gui):
    MainWindow()


def test_main_window_german(gui):
    Message.language = "german"

    MainWindow()
