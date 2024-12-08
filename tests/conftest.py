import os
from subprocess import run

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


@pytest.fixture(scope="session", autouse=True)
def pkexec():
    if "CI" in os.environ:
        run(["sudo", "ln", "/usr/bin/sudo", "/usr/bin/pkexec"])


@pytest.fixture()
def ci():
    if "CI" not in os.environ:
        pytest.skip("No CI")
