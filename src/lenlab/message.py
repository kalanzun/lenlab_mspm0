from textwrap import dedent

from attrs import asdict, frozen

from .language import Language


@frozen
class Message:
    english = ""
    german = ""

    def __str__(self):
        template = getattr(self, Language.language)
        template = dedent(template).strip()
        return template.format(**asdict(self))
