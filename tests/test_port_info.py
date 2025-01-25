import pytest
from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.launchpad.port_info import PortInfo


@pytest.fixture()
def available_ports(monkeypatch):
    available_ports = []
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: available_ports)
    return available_ports


def test_from_port_name():
    pi = PortInfo.from_name("COM0")
    assert not pi.is_available
    assert pi.name == "COM0"
    assert isinstance(pi.q_port_info, QSerialPortInfo)


def test_available_ports(available_ports):
    available_ports.append(QSerialPortInfo())

    (pi,) = PortInfo.available_ports()
    assert not pi.is_available
    assert pi.name == ""
    assert isinstance(pi.q_port_info, QSerialPortInfo)


def test_sort_key():
    pi = PortInfo("COM0")
    assert pi.sort_key == [0]
