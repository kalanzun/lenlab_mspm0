from textwrap import dedent

from attrs import asdict, frozen

from .language import Language


@frozen
class Message(Exception):
    english = ""
    german = ""

    progress = 0

    def head_and_body(self):
        template = getattr(self, Language.language) or "\n"
        message = template.format(**asdict(self))
        return message.split("\n", 1)

    def __str__(self):
        return self.head_and_body()[0]

    def long_form(self):
        head, body = self.head_and_body()
        body = dedent(body).strip()
        return f"{head}\n{body}"
