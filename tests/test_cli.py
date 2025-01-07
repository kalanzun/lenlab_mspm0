import sys

from lenlab.cli.cli import main


def test_cli(monkeypatch):
    monkeypatch.setattr(sys, "argv", [sys.argv[0], "blank"])
    main()


def test_main(monkeypatch):
    monkeypatch.setattr(sys, "argv", [sys.argv[0], "blank"])

    from lenlab import __main__

    assert __main__
