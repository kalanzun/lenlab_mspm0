import pytest

from lenlab.app import main
from lenlab.app.window import MainWindow


class MockApp:
    def exec(self):
        pass


@pytest.fixture()
def mock_app(monkeypatch):
    monkeypatch.setattr(main, "App", MockApp)


@pytest.fixture()
def no_show(monkeypatch):
    monkeypatch.setattr(MainWindow, "show", lambda self: None)


def test_main(mock_app, no_show):
    main.main()


def test_lenlab_main(mock_app, no_show):
    from lenlab import __main__

    assert __main__
