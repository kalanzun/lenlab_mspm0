from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QFileDialog

from lenlab.app.window import MainWindow
from lenlab.controller.lenlab import Lenlab
from lenlab.controller.report import Report
from lenlab.launchpad import rules


@pytest.fixture
def window(widgets):
    return MainWindow(Lenlab(), Report(), rules=True)


def test_main_window(window):
    assert window


def test_report(window, monkeypatch, tmp_path):
    tmp_file = tmp_path / "report.txt"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda parent, title, file_name, file_format: (tmp_file, file_format),
    )
    window.report_action.trigger()
    # it's empty without logging
    assert tmp_file.exists()


def test_rules(window, monkeypatch):
    monkeypatch.setattr(rules, "install_rules", mock := Mock(return_value=None))
    window.rules_action.trigger()
    assert mock.call_count == 1
