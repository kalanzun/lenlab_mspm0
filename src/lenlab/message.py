from textwrap import dedent

from .language import Language


class Message(Exception):
    english: str = ""
    german: str = ""

    def __str__(self):
        template = getattr(self, Language.language)
        template = dedent(template).strip()
        content = template.format(*self.args)
        return content
