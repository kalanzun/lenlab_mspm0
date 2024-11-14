from collections.abc import Callable

from PySide6.QtCore import QTimer


class SingleShotTimer(QTimer):
    interval: int = 400

    def __init__(self, callback: Callable[[], None], interval: int = 0):
        super().__init__()

        self.timeout.connect(callback)

        if interval:
            self.interval = interval

        self.setInterval(self.interval)
        self.setSingleShot(True)
