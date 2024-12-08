from dataclasses import dataclass
from pathlib import Path
from subprocess import run

import pytest

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


def test_install_rules_local(monkeypatch):
    monkeypatch.setattr(linux, "run", lambda *args, **kwargs: ...)
    linux.install_rules()


def test_rules():  # pragma: no cover
    pytest.skip("No Linux")
    # 'verify' does not work in CI
    run(["udevadm", "verify", "/etc/udev/rules.d/50-launchpad.rules"], check=True)


def test_check_permission():
    assert linux.check_permission(Path("/dev/null"))


def test_check_no_permission():
    assert not linux.check_permission(Path("/root"))


def test_get_group():
    assert linux.get_group(Path("/root")) == "root"


def test_get_user_groups():
    assert linux.get_user_groups()


def test_check_in_group():
    assert linux.check_group(Path.home())


def test_check_not_in_group_local():
    assert not linux.check_group(Path("/root"))


def test_check_not_in_group_ci(ci):  # pragma: no cover
    assert not linux.check_group(Path("/dev/ttyS0"))


def test_add_to_group_local(monkeypatch):
    monkeypatch.setattr(linux, "run", lambda *args, **kwargs: ...)
    linux.add_to_group(Path("/dev/null"))


def test_add_to_group_ci(monkeypatch, ci):  # pragma: no cover
    monkeypatch.setattr(linux, "pkexec", "sudo")
    linux.add_to_group(Path("/dev/ttyS0"))
    groups = run(["groups"], capture_output=True, text=True).stdout
    assert "tty" in groups


def test_check_in_group_ci(ci):  # pragma: no cover
    assert linux.check_group(Path("/dev/ttyS0"))
