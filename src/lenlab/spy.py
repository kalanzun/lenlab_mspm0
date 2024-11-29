from PySide6.QtTest import QSignalSpy

from .loop import Loop


class Spy(QSignalSpy):
    def __init__(self, signal):
        super().__init__(signal)

        self._signal = signal

    def get_single_arg(self):
        if self.count() == 1:
            return self.at(0)[0]

    def run_until(self) -> bool:
        if self.count():
            return True

        loop = Loop()
        return loop.run_until(self._signal)

    def run_until_single_arg(self):
        if self.run_until():
            return self.get_single_arg()
