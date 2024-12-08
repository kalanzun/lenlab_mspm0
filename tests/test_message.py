import pytest

from lenlab.message import Message


class Example(Message):
    english = "Example {0}"
    german = "Beispiel {0}"


def test_message():
    Message.language = "english"
    assert str(Example(1)) == "Example 1"


def test_german():
    Message.language = "german"
    assert str(Example(1)) == "Beispiel 1"


@pytest.mark.parametrize("cls", Message.__subclasses__())
def test_english_missing(cls):
    assert cls.english


@pytest.mark.parametrize("cls", Message.__subclasses__())
def test_german_missing(cls):
    assert cls.german
