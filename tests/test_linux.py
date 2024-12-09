from dataclasses import dataclass
from pathlib import Path
from subprocess import run

import pytest

from lenlab.controller import linux

pytestmark = pytest.mark.linux


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


def test_install_rules(monkeypatch):
    monkeypatch.setattr(linux, "pk_exec", lambda *args, **kwargs: ...)
    linux.install_rules()


def test_check_permission():
    assert linux.check_permission(Path("/dev/null"))


def test_check_no_permission():
    assert not linux.check_permission(Path("/root"))


def test_get_group():
    assert linux.get_group(Path("/dev/ttyS0")) == "dialout"


def test_get_user_groups():
    assert linux.get_user_groups()


def test_check_in_group():
    assert linux.check_group(Path.home())


def test_check_not_in_group():
    assert not linux.check_group(Path("/root"))


def test_add_to_group(monkeypatch):
    monkeypatch.setattr(linux, "pk_exec", lambda *args, **kwargs: ...)
    linux.add_to_group(Path("/dev/null"))


@pytest.mark.ci
class CI:
    @staticmethod
    def test_rules():  # pragma: no cover
        linux.install_rules()
        verify = run(["udevadm", "verify", "/etc/udev/rules.d/50-launchpad.rules"])
        assert verify.returncode == 0

    @staticmethod
    def test_check_not_in_group():  # pragma: no cover
        assert not linux.check_group(Path("/dev/ttyS0"))

    @staticmethod
    def test_add_to_group():  # pragma: no cover
        linux.add_to_group(Path("/dev/ttyS0"))
        # root privileges for sudo -u
        groups = run(
            ["sudo", "sudo", "-u", linux.get_user_name(), "groups"], capture_output=True, text=True
        ).stdout.strip()
        assert "dialout" in groups

    @staticmethod
    def test_check_in_group():  # pragma: no cover
        assert linux.check_group(Path("/dev/ttyS0"))
