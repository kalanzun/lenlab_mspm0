import pytest

from PySide6.QtCore import QCoreApplication


@pytest.fixture(scope="session")
def app() -> QCoreApplication:
    return QCoreApplication()
