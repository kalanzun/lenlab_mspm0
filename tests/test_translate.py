from lenlab.language import Language
from lenlab.translate import Translate, tr


def test_tr(monkeypatch):
    monkeypatch.setattr(Language, "language", "english")
    assert tr("english", "deutsch") == "english"


def test_tr_german(monkeypatch):
    monkeypatch.setattr(Language, "language", "german")
    assert tr("english", "deutsch") == "deutsch"


def test_translate(monkeypatch):
    monkeypatch.setattr(Language, "language", "english")
    assert str(Translate("english", "deutsch")) == "english"


def test_translate_german(monkeypatch):
    monkeypatch.setattr(Language, "language", "german")
    assert str(Translate("english", "deutsch")) == "deutsch"
