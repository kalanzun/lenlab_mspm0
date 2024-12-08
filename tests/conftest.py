import pytest

from lenlab.app.app import App


@pytest.fixture(scope="session", autouse=True)
def app():
    return App.get_instance()
