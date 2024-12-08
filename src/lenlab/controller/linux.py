import os
from pathlib import Path
from subprocess import run


# pkexec of PolicyKit
pkexec = "pkexec"

rules_path = Path("/etc/udev/rules.d/50-launchpad.rules")

launchpad_rules = b"""
ATTRS{idVendor}=="0451", ATTRS{idProduct}=="bef3", ENV{ID_MM_DEVICE_IGNORE}="1"
"""


def check_rules() -> bool:
    return rules_path.exists() and rules_path.read_bytes() == launchpad_rules


def su_write(path: Path, data: bytes) -> None:
    # tee of GNU coreutils
    run([pkexec, "tee", path], input=data)


def install_rules() -> None:
    su_write(rules_path, launchpad_rules)


def check_permission(port_path: Path) -> bool:
    return os.access(port_path, os.R_OK | os.W_OK)


def get_group(port_path: Path) -> str:
    return port_path.group()


def get_user():
    import pwd

    uid = os.getuid()
    return pwd.getpwuid(uid)


def get_user_groups():
    import grp

    user = get_user()
    return [grp.getgrgid(g).gr_name for g in os.getgrouplist(user.pw_name, user.pw_gid)]


def check_group(port_path: Path) -> bool:
    return get_group(port_path) in get_user_groups()


def add_to_group(port_path: Path) -> None:
    user = get_user().pw_name
    group = get_group(port_path)
    run([pkexec, "usermod", "-aG", group, user])
