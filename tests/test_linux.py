from dataclasses import dataclass
from pathlib import Path

from lenlab.controller import linux


@dataclass()
class MockPath:
    _exists: bool
    _content: bytes = b""

    def exists(self):
        return self._exists

    def read_bytes(self):
        return self._content


def test_check_rules(monkeypatch):
    monkeypatch.setattr(linux, "rules_path", MockPath(False))
    assert not linux.check_rules()


def test_check_rules_old(monkeypatch):
    monkeypatch.setattr(linux, "rules_path", MockPath(True))
    assert not linux.check_rules()


def test_check_rules_ok(monkeypatch):
    monkeypatch.setattr(linux, "rules_path", MockPath(True, linux.launchpad_rules))
    assert linux.check_rules()


def test_su_write(monkeypatch):
    monkeypatch.setattr(linux, "run", lambda *args, **kwargs: ...)
    linux.su_write(Path(), b"")


def test_install_rules(monkeypatch):
    # I have sudo on github actions
    # I could test the rule with udevadm test in an actual system
    monkeypatch.setattr(linux, "su_write", lambda *args, **kwargs: ...)
    linux.install_rules()


def test_check_permission():
    assert linux.check_permission(Path("/dev/null"))


def test_check_no_permission():
    assert not linux.check_permission(Path("/root"))


def test_get_group():
    assert linux.get_group(Path("/dev/null")) == "root"


def test_get_user_groups():
    assert linux.get_user_groups()


def test_check_in_group():
    assert linux.check_group(Path.home())


def test_check_not_in_group():
    assert not linux.check_group(Path("/root"))


def test_add_to_group(monkeypatch):
    # I could test with /dev/ttyS0 in group dialout
    monkeypatch.setattr(linux, "run", lambda *args, **kwargs: ...)
    linux.add_to_group(Path("/dev/null"))
