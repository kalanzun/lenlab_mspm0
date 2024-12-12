import os

import pytest
from PySide6.QtCore import QCoreApplication


def pytest_addoption(parser):
    parser.addoption(
        "--fw",
        action="store_true",
        default=False,
        help="run firmware tests",
    )
    parser.addoption(
        "--bsl",
        action="store_true",
        default=False,
        help="run BSL tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "firmware")
    config.addinivalue_line("markers", "bsl")
    config.addinivalue_line("markers", "ci")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "firmware" in item.keywords and not config.getoption("fw"):
            item.add_marker(pytest.mark.skip(reason="no firmware"))
        if "bsl" in item.keywords and not config.getoption("bsl"):
            item.add_marker(pytest.mark.skip(reason="no BSL"))
        if "ci" in item.keywords and "CI" not in os.environ:
            item.add_marker(pytest.mark.skip(reason="no CI"))


@pytest.fixture(scope="session", autouse=True)
def app():
    return QCoreApplication()
