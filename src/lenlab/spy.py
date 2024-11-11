from PySide6.QtTest import QSignalSpy

from lenlab.loop import loop_until


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

        return loop_until(self._signal, timeout=timeout)

    def run_until_single_arg(self, timeout=100):
        if self.run_until(timeout):
            return self.get_single_arg()
