from collections.abc import Callable

from PySide6.QtCore import QObject, Qt, Signal


class QueuedCall(QObject):
    trigger = Signal()

    def __init__(self, parent: QObject, slot: Callable[[], None]):
        super().__init__(parent)

        self.trigger.connect(slot, Qt.ConnectionType.QueuedConnection)
        self.trigger.connect(self.deleteLater, Qt.ConnectionType.QueuedConnection)
        self.trigger.emit()
