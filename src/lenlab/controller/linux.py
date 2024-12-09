import os
import sys
from pathlib import Path
from subprocess import run

rules_path = Path("/etc/udev/rules.d/50-launchpad.rules")

launchpad_rules = b"""
ATTRS{idVendor}=="0451", ATTRS{idProduct}=="bef3", ENV{ID_MM_DEVICE_IGNORE}="1"
"""


def is_linux() -> bool:
    return sys.platform == "linux"


def check_rules() -> bool:
    return rules_path.exists() and rules_path.read_bytes() == launchpad_rules


def pk_exec(args: list[str], **kwargs):
    # pkexec of PolicyKit
    run(["pkexec"] + args, **kwargs)


def pk_write(path: Path, data: bytes) -> None:
    # tee of GNU coreutils
    pk_exec(["tee", str(path)], input=data)


def install_rules() -> None:
    pk_write(rules_path, launchpad_rules)


def check_permission(port_path: Path) -> bool:
    return os.access(port_path, os.R_OK | os.W_OK)


def get_group(port_path: Path) -> str:
    return port_path.group()


def _get_user():
    import pwd

    uid = os.getuid()
    return pwd.getpwuid(uid)


def get_user_name() -> str:
    return _get_user().pw_name


def get_user_groups() -> list[str]:
    import grp

    _user = _get_user()
    return [grp.getgrgid(g).gr_name for g in os.getgrouplist(_user.pw_name, _user.pw_gid)]


def check_group(port_path: Path) -> bool:
    return get_group(port_path) in get_user_groups()


def add_to_group(port_path: Path) -> None:
    user = get_user_name()
    group = get_group(port_path)
    pk_exec(["usermod", "-aG", group, user])
