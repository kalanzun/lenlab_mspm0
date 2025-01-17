import sys

from lenlab.cli import main


def test_cli():
    main(["--preview"])


def test_main(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["lenlab", "--preview"])

    from lenlab import __main__

    assert __main__
