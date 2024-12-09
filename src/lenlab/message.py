class Message(Exception):
    language: str = "english"

    english: str = ""
    german: str = ""

    button: str = ""
    progress: int = 0

    def __init__(self, *args, callback=None):
        super().__init__(*args)
        self.callback = callback

    def __str__(self) -> str:
        template = getattr(self, self.language)
        template = "\n".join(line.strip() for line in template.splitlines())
        return template.format(*self.args)

    def short(self) -> str:
        template = getattr(self, self.language)
        template, *rest = template.split("\n", 1)
        template = template.strip()
        return template.format(*self.args)
