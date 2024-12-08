from lenlab.message import Message
from lenlab.vocabulary import Vocabulary as Vocab


def test_vocab():
    Message.language = "english"
    assert str(Vocab("Example", "Beispiel")) == "Example"


def test_german():
    Message.language = "german"
    assert str(Vocab("Example", "Beispiel")) == "Beispiel"
