from io import StringIO

from PySide6.QtCore import QObject

from ..launchpad.discovery import Discovery
from ..queued import QueuedCall


class Lenlab(QObject):
    def __init__(self):
        super().__init__()

        self.error_report = StringIO()

        self.discovery = Discovery()
        QueuedCall(self.discovery.find, self)
