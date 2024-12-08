import os

import pytest
from PySide6.QtCore import QCoreApplication

from lenlab.app.app import App


@pytest.fixture(scope="session", autouse=True)
def app():
    if "CI" not in os.environ:
        return App.get_instance()
    else:
        return QCoreApplication()


@pytest.fixture()
def gui():
    if "CI" in os.environ:
        pytest.skip("No GUI")


@pytest.fixture()
def ci():
    if "CI" not in os.environ:
        pytest.skip("No CI")
