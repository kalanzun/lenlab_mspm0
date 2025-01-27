from pathlib import Path
from subprocess import run

rules_path = Path("/etc/udev/rules.d/50-launchpad.rules")

rules_content = """
ATTRS{idVendor}=="0451", ATTRS{idProduct}=="bef3", ENV{ID_MM_DEVICE_IGNORE}="1"
"""


def pk_exec(args: list[str], **kwargs):
    # pkexec of PolicyKit
    run(["pkexec"] + args, **kwargs)


def pk_write(path: Path, content: str) -> None:
    # tee of GNU coreutils
    pk_exec(["tee", str(path)], input=content, capture_output=True, text=True)


def check_rules() -> bool:
    return rules_path.exists() and rules_path.read_text() == rules_content


def install_rules() -> None:
    pk_write(rules_path, rules_content)
