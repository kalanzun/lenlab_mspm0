from typing import Callable

from PySide6.QtCore import QTimer


class SingleShotTimer(QTimer):
    def __init__(self, callback: Callable[[], None], timeout: int = 100):
        super().__init__()

        self.setSingleShot(True)
        self.setInterval(timeout)
        self.timeout.connect(callback)
