import logging
from argparse import ArgumentParser

from PySide6.QtCore import QCoreApplication

from .sys_info import sys_info
from .flash import flash
from .profile import profile
from .app import app
from .practice import practice


def main() -> int:
    cli = [
        app,
        flash,
        practice,
        profile,
        sys_info,
    ]

    commands = {cmd.__name__: cmd for cmd in cli}

    parser = ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        choices=list(commands.keys()),
        default=cli[0].__name__,
    )
    parser.add_argument(
        "--log",
        nargs="?",
    )

    namespace, _ = parser.parse_known_args()
    if namespace.command != "app":
        application = QCoreApplication()  # noqa: F841

    if namespace.log:
        logging.basicConfig(filename=namespace.log, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    return commands[namespace.command]()
