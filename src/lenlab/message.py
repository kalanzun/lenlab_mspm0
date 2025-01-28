from textwrap import dedent

from .language import Language


class Message(Exception):
    english = ""
    german = ""

    progress = 0

    def __str__(self):
        template = getattr(self, Language.language).strip()
        first_line = template.split("\n", 1)[0].strip()
        return first_line.format(*self.args)

    def long_form(self):
        template = getattr(self, Language.language).strip() + "\n"
        head, body = template.split("\n", 1)
        body = dedent(body)
        return "\n".join((head, body)).format(*self.args)
