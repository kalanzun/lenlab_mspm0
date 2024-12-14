import pytest
from PySide6.QtCore import QCoreApplication

from lenlab.model.lenlab import Lenlab


@pytest.fixture(scope="session", autouse=True)
def app():
    return QCoreApplication()


@pytest.fixture()
def lenlab():
    return Lenlab()
