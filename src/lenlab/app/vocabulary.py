from dataclasses import dataclass

from ..message import Message


@dataclass(frozen=True, slots=True)
class Word:
    english: str
    german: str

    def __str__(self):
        return getattr(self, Message.language)


@dataclass(frozen=True, slots=True)
class Vocabulary(Word):
    program = Word("Program", "Programmieren")

    start = Word("Start", "Start")
    stop = Word("Stop", "Stop")
    cancel = Word("Cancel", "Abbrechen")
    retry = Word("Retry", "Neuer Versuch")
    hide = Word("Hide", "Ausblenden")
    discard = Word("Discard", "Verwerfen")
    save_as = Word("Save As", "Speichern unter")
    automatic_save = Word("Automatic save", "Automatisch Speichern")
    save_image = Word("Save Image", "Bild Speichern")

    time = Word("Time", "Zeit")
    interval = Word("Interval", "Intervall")
    hours = Word("hours", "Stunden")
    minutes = Word("minutes", "Minuten")
    seconds = Word("seconds", "Sekunden")

    voltage = Word("Voltage", "Spannung")
    volt = Word("volt", "Volt")
