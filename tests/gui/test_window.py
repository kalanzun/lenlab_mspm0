from io import StringIO

import pytest
from PySide6.QtWidgets import QFileDialog

from lenlab.app.window import MainWindow
from lenlab.launchpad.discovery import Discovery


@pytest.mark.gui
def test_window():
    error_report = StringIO()
    discovery = Discovery()
    MainWindow(error_report, discovery)


@pytest.mark.gui
def test_save_error_report(monkeypatch, tmp_path):
    error_report = StringIO("Example")
    discovery = Discovery()
    window = MainWindow(error_report, discovery)

    file_path = tmp_path / "lenlab8-error-report.txt"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda parent, caption, dir, filter: (str(file_path), None)
    )
    window.save_error_report()

    assert file_path.read_text() == "Example"


@pytest.mark.gui
def test_save_error_report_cancel(monkeypatch):
    error_report = StringIO("Example")
    discovery = Discovery()
    window = MainWindow(error_report, discovery)

    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda parent, caption, dir, filter: (None, None)
    )
    window.save_error_report()
