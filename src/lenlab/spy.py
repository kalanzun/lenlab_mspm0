from PySide6.QtTest import QSignalSpy


class Spy(QSignalSpy):
    def get_single_arg(self):
        if self.count() == 1:
            return self.at(0)[0]

    def is_single_message(self, cls) -> bool:
        return isinstance(self.get_single_arg(), cls)
