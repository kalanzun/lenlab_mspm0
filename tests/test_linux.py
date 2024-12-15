from subprocess import run

import pytest

from lenlab.controller import linux


def test_pk_exec(monkeypatch):
    monkeypatch.setattr(linux, "run", lambda *args, **kwargs: None)
    linux.pk_exec(["ls"])


@pytest.fixture()
def tmp_rules(monkeypatch, tmp_path):
    tmp_rules = tmp_path / linux.rules_path.name
    monkeypatch.setattr(linux, "rules_path", tmp_rules)
    return tmp_rules


def test_check_no_rules(tmp_rules):
    assert not linux.check_rules()


def test_check_rules_empty(tmp_rules):
    tmp_rules.write_text("\n")
    assert not linux.check_rules()


@pytest.fixture()
def mock_pk_exec(monkeypatch):
    monkeypatch.setattr(linux, "pk_exec", run)


def test_install_rules(tmp_rules, mock_pk_exec):
    linux.install_rules()
    assert linux.check_rules()


@pytest.mark.linux
def test_rules(tmp_rules, mock_pk_exec):
    linux.install_rules()
    result = run(["udevadm", "verify", tmp_rules])
    assert result.returncode == 0
