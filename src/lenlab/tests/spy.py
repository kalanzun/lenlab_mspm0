from PySide6.QtCore import QEventLoop
from PySide6.QtTest import QSignalSpy

from lenlab.singleshot import SingleShotTimer


class Spy(QSignalSpy):
    def __init__(self, signal):
        super().__init__(signal)

        self._signal = signal

    def get_single_arg(self):
        if self.count() == 1:
            return self.at(0)[0]

    def run_until(self, timeout=100):
        if self.count():
            return True

        loop = QEventLoop()
        _connection = self._signal.connect(lambda: loop.exit(0))
        timer = SingleShotTimer(lambda: loop.exit(1), timeout)

        timer.start()
        _error = loop.exec()
        timer.stop()
        self._signal.disconnect(_connection)

        return not _error

    def run_until_single_arg(self, timeout=100):
        if self.run_until(timeout):
            return self.get_single_arg()
