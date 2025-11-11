from attrs import frozen

from .language import Language


def tr(english: str, german: str) -> str:
    if Language.language == "german":
        return german

    return english


@frozen
class Translate:
    english: str
    german: str

    def __str__(self):
        return getattr(self, Language.language)
