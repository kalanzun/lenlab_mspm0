class Message(Exception):
    english = ""
    german = ""

    language = "english"

    def __str__(self):
        template = getattr(self, self.language)
        template = "\n".join(line.strip() for line in template.splitlines())
        return template.format(*self.args)
