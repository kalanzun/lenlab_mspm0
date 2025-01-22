import pytest
from PySide6.QtCore import QObject, Signal, Slot

from lenlab.app import main


class MockApp:
    def exec(self):
        pass


class MockDiscovery(QObject):
    available = Signal()

    def find(self):
        self.available.emit()

    @Slot()
    def probe(self):
        pass


class MockWindow:
    def __init__(self, error_report, discovery):
        self.error_report = error_report
        self.discovery = discovery

    def show(self):
        pass


@pytest.fixture()
def mock_app(monkeypatch):
    monkeypatch.setattr(main, "App", MockApp)
    monkeypatch.setattr(main, "Discovery", MockDiscovery)
    monkeypatch.setattr(main, "MainWindow", MockWindow)


def test_main(mock_app):
    main.main()


def test_lenlab_main(mock_app):
    from lenlab import __main__

    assert __main__
