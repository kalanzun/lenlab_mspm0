from typing import Any

from PySide6.QtTest import QSignalSpy


class Spy(QSignalSpy):
    def __init__(self, signal):
        super().__init__(signal)

        self._signal = signal

    def get_single_arg(self) -> Any:
        if self.count() == 1:
            return self.at(0)[0]
