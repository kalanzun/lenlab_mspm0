import pytest
from PySide6.QtWidgets import QFileDialog

from lenlab.app.window import MainWindow
from lenlab.device.lenlab import Lenlab


@pytest.mark.gui
def test_window():
    assert MainWindow(Lenlab())


@pytest.mark.gui
def test_save_error_report(monkeypatch, tmp_path):
    window = MainWindow(Lenlab())
    window.lenlab.error_report.write("Example\n")

    file_path = tmp_path / "lenlab8-error-report.txt"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda parent, caption, dir, filter: (str(file_path), None)
    )
    window.save_error_report()

    assert file_path.read_text() == "Example\n"


@pytest.mark.gui
def test_save_error_report_cancel(monkeypatch):
    window = MainWindow(Lenlab())
    window.lenlab.error_report.write("Example\n")

    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda parent, caption, dir, filter: (None, None)
    )
    window.save_error_report()
