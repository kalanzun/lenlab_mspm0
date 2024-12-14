from lenlab.language import Language
from lenlab.message import Message


class Example(Message):
    english = "Example"
    german = "Beispiel"


def test_message():
    message = Example()
    assert str(message) == "Example"


def test_german(monkeypatch):
    monkeypatch.setattr(Language, "language", "german")
    message = Example()
    assert str(message) == "Beispiel"
