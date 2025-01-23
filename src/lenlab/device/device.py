from PySide6.QtCore import QObject

from .lenlab import Lenlab


class Device(QObject):
    def __init__(self, lenlab: Lenlab):
        super().__init__()

        self.lenlab = lenlab
