from dataclasses import dataclass
from enum import IntEnum

from PySide6.QtCore import QLocale


class Category(IntEnum):
    INFO = 0
    WARNING = 1
    ERROR = 2


@dataclass(frozen=True)
class Message:
    category: Category
    en: str
    de: str | None = None

    def get_text(self):
        lang = QLocale().language()
        if lang == QLocale.Language.German and self.de is not None:
            return self.de
        else:
            return self.en


MORE_THAN_ONE_LAUNCHPAD_FOUND = Message(
    Category.ERROR,
    en="""More than one Launchpad found
    Lenlab can operate only one Launchpad at a time. Please connect a single Launchpad to the computer.""",
    de="""Mehr als ein Launchpad gefunden
    Lenlab arbeitet nur mit einem Launchpad zusammen. Bitte ein einzelnes Lanuchpad mit dem Computer verbinden.""",
)

TIVA_LAUNCHPAD_FOUND = Message(
    Category.ERROR,
    en="""Tiva C-Series Launchpad found
    This Lenlab Version 8 works with the Launchpad LP-MSPM0G3507.
    Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
    works with the Tiva C-Series Launchpad EK-TM4C123GXL.""",
    de="""Tiva C-Serie Launchpad gefunden
    Dieses Lenlab Version 8 arbeitet mit dem Lanuchpad LP-MSPM0G3507 zusammen.
    Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
    arbeitet mit dem Tiva C-Serie Launchpad EK-TM4C123GXL zusammen.""",
)

NO_LAUNCHPAD_FOUND = Message(
    Category.ERROR,
    en="""No Launchpad found
    Connect the Launchpad via USB to the computer.""",
    de="""Kein Launchpad gefunden
    Bitte das Launchpad über USB mit dem Computer verbinden.""",
)

PERMISSION_ERROR = Message(
    Category.ERROR,
    en="""Permission error on Launchpad connection
    Lenlab requires unique access to the serial communication with the Lanuchpad.
    Maybe another instance of Lenlab is running and blocks the access?""",
    de="""Keine Zugriffsberechtigung auf die Verbindung mit dem Launchpad
    Lenlab braucht alleinigen Zugriff auf die serielle Kommunikation mit dem Launchpad.
    Vielleicht läuft noch eine andere Instanz von Lenlab und blockiert den Zugriff?""",
)
