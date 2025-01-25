import re
from typing import Self

from attrs import frozen
from PySide6.QtSerialPort import QSerialPortInfo


@frozen
class PortInfo:
    name: str = ""
    vid: int = 0
    pid: int = 0

    is_available: bool = False
    q_port_info: QSerialPortInfo | None = None

    @classmethod
    def from_q_port_info(cls, q_port_info: QSerialPortInfo, name: str | None = None) -> Self:
        return cls(
            name=name or q_port_info.portName(),
            vid=q_port_info.vendorIdentifier(),
            pid=q_port_info.productIdentifier(),
            is_available=not q_port_info.isNull(),
            q_port_info=q_port_info,
        )

    @classmethod
    def from_name(cls, name: str) -> Self:
        return cls.from_q_port_info(QSerialPortInfo(name), name=name)

    @classmethod
    def available_ports(cls) -> list[Self]:
        return [cls.from_q_port_info(qpi) for qpi in QSerialPortInfo.availablePorts()]

    @property
    def sort_key(self) -> list[int]:
        return [int(n) for n in re.findall(r"\d+", self.name)]
