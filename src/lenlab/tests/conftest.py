from typing import Iterable

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtSerialPort import QSerialPortInfo


@pytest.fixture(scope="session", autouse=True)
def app() -> QCoreApplication:
    return QCoreApplication()


@pytest.fixture(scope="session")
def port_infos() -> Iterable[QSerialPortInfo]:
    return QSerialPortInfo.availablePorts()
