from lenlab.message import Message


class Dedent(Message):
    english = """headline
    
    content"""


def test_dedent():
    message = Dedent()
    assert str(message) == "headline"
    assert message.long_form() == "headline\n\ncontent\n"


class Newline(Message):
    english = """
    headline

    content
    """


def test_newline():
    message = Newline()
    assert str(message) == "headline"
    assert message.long_form() == "headline\n\ncontent\n"
