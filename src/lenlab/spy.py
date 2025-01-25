from typing import Any

from PySide6.QtTest import QSignalSpy


class Spy(QSignalSpy):
    def get_single_arg(self) -> Any:
        assert self.count() == 1
        return self.at(0)[0]

    def check_single_message(self, message_class: Any) -> None:
        message = self.get_single_arg()
        assert isinstance(message, message_class)
