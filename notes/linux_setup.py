from pathlib import Path
from subprocess import run


launchpad_rules = b'ATTRS{idVendor}=="0451", ATTRS{idProduct}=="bef3", ENV{ID_MM_DEVICE_IGNORE}="1"\n'


def main():
    rules = Path("/etc/udev/rules.d/50-lenlab.rules")
    if not rules.exists() or rules.read_bytes() != launchpad_rules:
        # pkexec of PolKit
        # sed of GNU coreutils
        run(["pkexec", "sed", "-n", f"w {rules}"], input=launchpad_rules)


if __name__ == "__main__":
    main()
