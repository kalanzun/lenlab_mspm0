from dataclasses import dataclass
from enum import IntEnum

from PySide6.QtCore import QLocale


class Category(IntEnum):
    ERROR = 0
    WARNING = 1
    INFO = 2


@dataclass(frozen=True)
class Message:
    category: Category
    english: str
    german: str | None = None

    def get_text(self, language: QLocale.Language):
        if language == QLocale.Language.German and self.german is not None:
            text = self.german
        else:
            text = self.english

        return "\n".join(line.strip() for line in text.splitlines())


MORE_THAN_ONE_LAUNCHPAD_FOUND = Message(
    Category.ERROR,
    english="""More than one Launchpad found
        Lenlab can operate only one Launchpad at a time.
        Please connect a single Launchpad to the computer.""",
    german="""Mehr als ein Launchpad gefunden
        Lenlab arbeitet nur mit einem Launchpad zusammen.
        Bitte ein einzelnes Lanuchpad mit dem Computer verbinden.""",
)

TIVA_LAUNCHPAD_FOUND = Message(
    Category.WARNING,
    english="""Tiva C-Series Launchpad found
        This Lenlab Version 8 works with the Launchpad LP-MSPM0G3507.
        Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
        works with the Tiva C-Series Launchpad EK-TM4C123GXL.""",
    german="""Tiva C-Serie Launchpad gefunden
        Dieses Lenlab in Version 8 funktioniert mit dem Lanuchpad LP-MSPM0G3507.
        Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
        funktioniert mit dem Tiva C-Serie Launchpad EK-TM4C123GXL.""",
)

NO_LAUNCHPAD_FOUND = Message(
    Category.WARNING,
    english="""No Launchpad found
        Connect the Launchpad via USB to the computer.""",
    german="""Kein Launchpad gefunden
        Bitte das Launchpad über USB mit dem Computer verbinden.""",
)

PERMISSION_ERROR = Message(
    Category.ERROR,
    english="""Permission error on Launchpad connection
        Lenlab requires unique access to the serial communication with the Lanuchpad.
        Maybe another instance of Lenlab is running and blocks the access?""",
    german="""Keine Zugriffsberechtigung auf die Verbindung mit dem Launchpad
        Lenlab braucht alleinigen Zugriff auf die serielle Kommunikation mit dem Launchpad.
        Vielleicht läuft noch eine andere Instanz von Lenlab und blockiert den Zugriff?""",
)

RESOURCE_ERROR = Message(
    Category.ERROR,
    english="""Connection lost
        The Launchpad vanished. Please reconnect it to the computer.""",
    german="""Verbindung verloren
        Das Lanuchpad ist verschwunden. Bitte wieder mit dem Computer verbinden.""",
)

CONNECTED = Message(
    Category.INFO,
    english="""Launchpad connected""",
    german="""Launchpad verbunden""",
)
