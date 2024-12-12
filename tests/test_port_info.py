from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.model.port_info import PortInfo


def test_from_q_port_info():
    PortInfo.from_q_port_info(QSerialPortInfo())


def test_available_ports(monkeypatch):
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [QSerialPortInfo()])
    PortInfo.available_ports()


def test_properties():
    pi = PortInfo.from_q_port_info(QSerialPortInfo())
    assert pi.vid_pid == (0, 0)
    assert pi.sort_key == []
