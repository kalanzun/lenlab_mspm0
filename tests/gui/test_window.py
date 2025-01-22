import pytest

from lenlab.app.window import MainWindow
from lenlab.launchpad.discovery import Discovery


@pytest.mark.gui
def test_window():
    discovery = Discovery()
    MainWindow(discovery)
