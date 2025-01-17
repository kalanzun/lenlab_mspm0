import pytest
from PySide6.QtCore import QCoreApplication


@pytest.fixture(scope="session", autouse=True)
def app():
    return QCoreApplication()
