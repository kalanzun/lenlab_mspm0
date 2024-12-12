from . import language


class Message(Exception):
    english: str = ""
    german: str = ""

    progress: int = 0

    def __str__(self):
        template = getattr(self, language.language)
        template = "\n".join(line.strip() for line in template.splitlines())
        return template.format(*self.args)
