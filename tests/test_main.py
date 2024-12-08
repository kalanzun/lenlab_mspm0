import sys

from lenlab.app.app import App
from lenlab.app.window import MainWindow


def test_main(monkeypatch, gui):
    monkeypatch.setattr(App, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: None)
    monkeypatch.setattr(sys, "exit", lambda ret_code: None)
    from lenlab import __main__  # noqa: F401
