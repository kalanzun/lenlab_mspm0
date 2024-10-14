"""Translated information message to the user, error message, or help text.

Define a new message as subclass of Message at module-level. Pass around an object of it.
When printing, print(Message()), widget.setText(str(Message())), it chooses the language
according to the global language setting (Message.language).
"""


class Message(Exception):
    language: str = "english"

    english: str = ""
    german: str = ""

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        assert cls.english, "English message missing"
        assert cls.german, "German message missing"

    def __str__(self):
        template = getattr(self, self.language)
        template = "\n".join(line.strip() for line in template.splitlines())
        return template.format(*self.args)
