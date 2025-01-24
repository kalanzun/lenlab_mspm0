from typing import Any

from PySide6.QtTest import QSignalSpy

from .message import Message


class Spy(QSignalSpy):
    def __init__(self, signal):
        super().__init__(signal)

        self._signal = signal

    def get_single_arg(self) -> Any:
        if self.count() == 1:
            return self.at(0)[0]

    def check_single_message(self, message_class: type[Message]):
        __tracebackhide__ = True

        msg = self.get_single_arg()
        assert msg is not None, "no message received"
        assert isinstance(msg, message_class), f"{type(msg)} is not {message_class}"
