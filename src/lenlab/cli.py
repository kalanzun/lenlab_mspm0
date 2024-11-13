import logging
import sys
from argparse import ArgumentParser

from PySide6.QtCore import QCoreApplication

commands = {}


def command(func):
    commands[func.__name__] = func
    return func


@command
def app():
    return 0


@command
def sys_info():
    from lenlab.sys_info import sys_info

    sys_info()
    return 0


@command
def profile():
    from lenlab.profile import profile

    cli_app = QCoreApplication()  # noqa: F841
    profile()
    return 0


@command
def flash():
    from lenlab.flash import flash

    cli_app = QCoreApplication()  # noqa: F841
    flash()
    return 0


@command
def exercise():
    from lenlab.exercise import exercise

    cli_app = QCoreApplication()  # noqa: F841
    exercise()
    return 0


def main():
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser()

    keys = list(commands.keys())
    parser.add_argument(
        "command",
        nargs="?",
        choices=keys,
        default=keys[0],
    )

    parser.add_argument(
        "--log",
        nargs="?",
    )

    options = parser.parse_args()
    if options.log:
        handler = logging.FileHandler(options.log, mode="w", encoding="utf-8")
        logging.getLogger().addHandler(handler)

    return commands[options.command]()


if __name__ == "__main__":
    sys.exit(main())
