import re
from typing import Self

from attrs import frozen
from PySide6.QtSerialPort import QSerialPortInfo


@frozen
class PortInfo:
    name: str
    vid: int
    pid: int

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
    def available_ports(cls) -> list[Self]:
        return [cls.from_q_port_info(qpi) for qpi in QSerialPortInfo.availablePorts()]

    @property
    def vid_pid(self) -> tuple[int, int]:
        return self.vid, self.pid

    @property
    def sort_key(self) -> list[int]:
        return [int(n) for n in re.findall(r"\d+", self.name)]
