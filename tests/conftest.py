import os
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QApplication, QFileDialog


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
    parser.addoption(
        "--port",
        help="launchpad port name",
    )


@pytest.fixture(scope="session")
def firmware(request):
    if not request.config.getoption("fw"):
        pytest.skip("no firmware")


@pytest.fixture(scope="session")
def bsl(request):
    if not request.config.getoption("bsl"):
        pytest.skip("no BSL")


@pytest.fixture(scope="session")
def linux():
    if sys.platform != "linux":
        pytest.skip(reason="No Linux")


@pytest.fixture(scope="session")
def qt_widgets():
    if "CI" in os.environ:
        pytest.skip(reason="No Qt Widgets")


@pytest.fixture(scope="session", autouse=True)
def app():
    if "CI" in os.environ:
        # No Qt Widgets in CI
        return QCoreApplication()

    else:
        return QApplication()


@pytest.fixture(scope="module")
def port(request):
    port = QSerialPort(QSerialPortInfo(request.config.getoption("--port")))
    if not port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
        pytest.skip(port.errorString())

    port.clear()
    port.setBaudRate(1_000_000)
    yield port
    port.close()


@pytest.fixture(scope="session")
def output():
    output = Path("output")
    output.mkdir(exist_ok=True)
    return output


class SaveFile:
    def __init__(self, base_path):
        self.base_path = base_path
        self.cancel = False

    def __call__(self, parent, title, file_name, file_format):
        if self.cancel:
            return "", ""

        self.file_path = self.base_path / file_name
        return str(self.file_path), file_format

    def read_text(self):
        return self.file_path.read_text(encoding="utf-8")

    def read_bytes(self):
        return self.file_path.read_bytes()


@pytest.fixture()
def save_file(monkeypatch, output):
    save_file = SaveFile(output)
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        save_file,
    )
    return save_file
