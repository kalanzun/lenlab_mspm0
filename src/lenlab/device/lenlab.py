from io import StringIO

from PySide6.QtCore import QObject, Qt, Signal, Slot

from ..launchpad.discovery import Discovery


class Lenlab(QObject):
    startup = Signal()

    def __init__(self):
        super().__init__()

        self.error_report = StringIO()

        self.discovery = Discovery()

        self.startup.connect(self.on_startup, Qt.ConnectionType.QueuedConnection)
        self.startup.emit()

    @Slot()
    def on_startup(self):
        self.discovery.find()
