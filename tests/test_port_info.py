from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.model.port_info import PortInfo


def test_available_ports(monkeypatch):
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [QSerialPortInfo()])
    available_ports = PortInfo.available_ports()
    (pi,) = available_ports
    assert pi.name == ""


def test_from_port_name():
    pi = PortInfo.from_port_name("")
    assert pi.name == ""


def test_sort_key():
    assert PortInfo("COM10").sort_key == [10]
