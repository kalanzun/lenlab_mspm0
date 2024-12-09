import sys

import pytest

from lenlab.app.app import App
from lenlab.app.window import MainWindow


@pytest.mark.gui
def test_main(monkeypatch):
    monkeypatch.setattr(App, "exec", lambda self: 0)
    monkeypatch.setattr(MainWindow, "show", lambda self: None)
    monkeypatch.setattr(sys, "exit", lambda ret_code: None)
    from lenlab import __main__  # noqa: F401
