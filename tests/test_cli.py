import sys

from lenlab.cli import main


def test_cli():
    main(["--preview"])


def test_main(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["lenlab", "--preview"])

    from lenlab import __main__

    assert __main__


def test_port_arg():
    main(["--preview", "--port", "COM0"])
