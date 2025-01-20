import os
import sys

import pytest
from PySide6.QtCore import QCoreApplication


def pytest_configure(config):
    config.addinivalue_line("markers", "ci")
    config.addinivalue_line("markers", "gui")
    config.addinivalue_line("markers", "linux")


def pytest_collection_modifyitems(config, items):  # pragma: no cover
    for item in items:
        if "ci" in item.keywords and "CI" not in os.environ:
            item.add_marker(pytest.mark.skip(reason="No CI"))
        if "gui" in item.keywords and "CI" in os.environ:
            item.add_marker(pytest.mark.skip(reason="No GUI"))
        if "linux" in item.keywords and sys.platform != "linux":
            item.add_marker(pytest.mark.skip(reason="No Linux"))


@pytest.fixture(scope="session", autouse=True)
def app():
    return QCoreApplication()
