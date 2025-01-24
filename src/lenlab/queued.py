from PySide6.QtCore import QObject, Qt, Signal


class QueuedCall(QObject):
    trigger = Signal()

    def __init__(self, function, parent):
        super().__init__(parent)

        self.trigger.connect(function, Qt.ConnectionType.QueuedConnection)
        self.trigger.connect(self.deleteLater, Qt.ConnectionType.QueuedConnection)
        self.trigger.emit()
