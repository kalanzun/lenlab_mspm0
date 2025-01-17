from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.model.port_info import PortInfo


def test_available_ports(monkeypatch):
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [QSerialPortInfo()])
    available_ports = PortInfo.available_ports()
    pi, = available_ports
    assert pi.name == ""
