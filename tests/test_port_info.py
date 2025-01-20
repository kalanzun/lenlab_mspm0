import pytest
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from lenlab.launchpad.port_info import PortInfo


@pytest.fixture()
def available_ports(monkeypatch):
    available_ports = []
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: available_ports)
    return available_ports


def test_from_port_name():
    pi = PortInfo.from_name("COM0")
    assert isinstance(pi.q_port_info, QSerialPortInfo)


def test_available_ports(available_ports):
    available_ports.append(QSerialPortInfo("COM0"))

    (pi,) = PortInfo.available_ports()
    assert isinstance(pi.q_port_info, QSerialPortInfo)


def test_sort_key():
    pi = PortInfo("COM0")
    assert pi.sort_key == [0]


def test_create_port():
    pi = PortInfo("COM0")
    port = pi.create_port()
    assert isinstance(port, QSerialPort)
