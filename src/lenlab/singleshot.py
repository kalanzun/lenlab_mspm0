from collections.abc import Callable

from PySide6.QtCore import QTimer


class SingleShotTimer(QTimer):
    def __init__(self, callback: Callable[[], None], timeout: int = 100):
        super().__init__()

        self.timeout.connect(callback)
        self.setInterval(timeout)
        self.setSingleShot(True)
