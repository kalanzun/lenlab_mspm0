from PySide6.QtCore import QObject
from PySide6.QtSerialPort import QSerialPort

from ..model.port_info import PortInfo


class Terminal(QObject):
    port: QSerialPort
    port_info: PortInfo

    def __init__(self, port_info: PortInfo):
        super().__init__()
        self.port_info = port_info
