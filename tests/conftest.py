import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from attrs import define
from PySide6.QtCore import QCoreApplication, QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import QApplication

from lenlab.app.save_as import SaveAs


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


@define
class MockFileObject:
    value: str | bytes

    def write(self, value: str | bytes):
        assert type(value) is type(self.value)
        self.value += value


@define
class MockPath:
    name: str = "data.csv"
    mock_file_object: MockFileObject | None = None

    @contextmanager
    def open(self, mode, *, encoding):
        assert mode in {"w", "wb", "a", "ab"}
        assert encoding == "utf-8"

        if mode == "w":
            self.mock_file_object = MockFileObject("")
        elif mode == "wb":
            self.mock_file_object = MockFileObject(b"")

        yield self.mock_file_object

    def write_bytes(self, value: bytes):
        self.mock_file_object = MockFileObject(value)

    def write_text(self, value: str):
        self.mock_file_object = MockFileObject(value)

    def read_bytes(self) -> bytes:
        assert isinstance(self.mock_file_object.value, bytes)
        return self.mock_file_object.value

    def read_text(self) -> str:
        assert isinstance(self.mock_file_object.value, str)
        return self.mock_file_object.value

    def get_line_count(self) -> int:
        assert isinstance(self.mock_file_object.value, str)
        return self.mock_file_object.value.count("\n")


@pytest.fixture()
def mock_path():
    mock_path = MockPath()
    return mock_path


@pytest.fixture()
def mock_save_as(monkeypatch, mock_path):
    def mock_show(self):
        self.save_as.emit(mock_path)

    monkeypatch.setattr(SaveAs, "show", mock_show)
    return mock_path
