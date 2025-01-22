import re
from typing import Self

from attrs import frozen
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


@frozen
class PortInfo:
    name: str = ""
    vid: int = 0
    pid: int = 0

    q_port_info: QSerialPortInfo | None = None

    @classmethod
    def from_q_port_info(cls, q_port_info: QSerialPortInfo) -> Self:
        return cls(
            name=q_port_info.portName(),
            vid=q_port_info.vendorIdentifier(),
            pid=q_port_info.productIdentifier(),
            q_port_info=q_port_info,
        )

    @classmethod
    def from_name(cls, name: str) -> Self | None:
        q_port_info = QSerialPortInfo(name)
        if not q_port_info.isNull():
            return cls.from_q_port_info(q_port_info)

    @classmethod
    def available_ports(cls) -> list[Self]:
        return [cls.from_q_port_info(qpi) for qpi in QSerialPortInfo.availablePorts()]

    @property
    def sort_key(self) -> list[int]:
        return [int(n) for n in re.findall(r"\d+", self.name)]

    def create_port(self) -> QSerialPort:
        return QSerialPort(self.q_port_info)
