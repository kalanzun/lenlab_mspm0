from dataclasses import dataclass

from .message import Message


@dataclass(frozen=True, slots=True)
class Word:
    english: str
    german: str

    def __str__(self):
        return getattr(self, Message.language)


@dataclass(frozen=True, slots=True)
class Vocabulary(Word):
    retry = Word("Retry", "Neuer Versuch")
