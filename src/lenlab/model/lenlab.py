from PySide6.QtCore import QObject, Signal

from ..message import Message


class Lenlab(QObject):
    port_infos: list

    error = Signal(Message)
