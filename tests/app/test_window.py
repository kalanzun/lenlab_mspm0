import logging
from unittest.mock import Mock

import pytest

from lenlab.app.window import MainWindow
from lenlab.controller.lenlab import Lenlab
from lenlab.controller.report import Report
from lenlab.launchpad import rules

logger = logging.getLogger(__name__)


@pytest.fixture
def window(qt_widgets):
    return MainWindow(Lenlab(), Report(), rules=True)


def test_main_window(window):
    assert window


def test_rules(window, monkeypatch):
    monkeypatch.setattr(rules, "install_rules", mock := Mock(return_value=None))
    window.rules_action.trigger()
    assert mock.call_count == 1


def test_save_report(window, save_as_output):
    logger.info("Hi there!")

    window.save_report_triggered()
    content = save_as_output["file_path"].read_text()
    assert content
