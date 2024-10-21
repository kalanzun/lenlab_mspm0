from PySide6.QtCore import QEventLoop
from PySide6.QtTest import QSignalSpy

from .singleshot import SingleShotTimer


class Spy(QSignalSpy):
    def __init__(self, signal, timeout=100):
        super().__init__(signal)

        self._signal = signal
        self._timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return

        if self.count() == 1:
            return

        loop = QEventLoop()
        self._signal.connect(loop.quit)
        timer = SingleShotTimer(loop.quit, self._timeout)

        timer.start()
        loop.exec()
        self._signal.disconnect(loop.quit)

    def get_single(self):
        if self.count() == 1:
            return self.at(0)[0]
