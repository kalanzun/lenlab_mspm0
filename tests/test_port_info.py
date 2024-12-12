import pytest
from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.model.port_info import PortInfo


@pytest.fixture()
def port_info():
    return PortInfo.from_q_port_info(QSerialPortInfo())


def test_port_info(port_info):
    assert isinstance(port_info, PortInfo)
    assert port_info.vid_pid == (0, 0)
    assert port_info.sort_key == []


def test_available_ports(monkeypatch):
    monkeypatch.setattr(QSerialPortInfo, "availablePorts", lambda: [QSerialPortInfo()])
    port_infos = PortInfo.available_ports()
    assert len(port_infos) == 1
    assert isinstance(port_infos[0], PortInfo)
