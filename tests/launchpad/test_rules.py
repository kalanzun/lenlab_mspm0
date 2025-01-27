import sys
from subprocess import run

import pytest

from lenlab.launchpad import rules


def test_pk_exec(monkeypatch):
    monkeypatch.setattr(rules, "run", lambda *args, **kwargs: None)
    rules.pk_exec(["ls"])


def test_pk_write(monkeypatch):
    monkeypatch.setattr(rules, "run", lambda *args, **kwargs: None)
    rules.pk_write(rules.rules_path, "content")


@pytest.fixture()
def tmp_rules(monkeypatch, tmp_path):
    tmp_rules = tmp_path / rules.rules_path.name
    monkeypatch.setattr(rules, "rules_path", tmp_rules)
    return tmp_rules


def test_check_no_rules(tmp_rules):
    assert not rules.check_rules()


def test_check_rules_empty(tmp_rules):
    tmp_rules.write_text("\n")
    assert not rules.check_rules()


@pytest.fixture()
def mock_pk_exec(monkeypatch):
    monkeypatch.setattr(rules, "pk_exec", run)


@pytest.fixture()
def mock_pk_write(monkeypatch, mock_pk_exec):
    if sys.platform == "win32":  # no tee on windows
        monkeypatch.setattr(rules, "pk_write", lambda path, content: path.write_text(content))


def test_install_rules(tmp_rules, mock_pk_write):
    rules.install_rules()
    assert rules.check_rules()


def test_rules(linux, tmp_rules, mock_pk_exec):
    rules.install_rules()
    result = run(["udevadm", "verify", tmp_rules])
    assert result.returncode == 0
