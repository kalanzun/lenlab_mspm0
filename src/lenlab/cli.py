import logging
import signal
from argparse import ArgumentParser

from PySide6.QtCore import QCoreApplication

from .loop import ReturnCode
from .sys_info import sys_info
from .flash import flash
from .profile import profile
from .app import app
from .practice import practice


def main() -> int:
    logging.basicConfig(level=logging.INFO)

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
        signal.signal(signal.SIGINT, lambda signum, frame: application.exit(ReturnCode.KEYBOARD_INTERRUPT))

    if namespace.log:
        handler = logging.FileHandler(namespace.log, mode="w", encoding="utf-8")
        logging.getLogger().addHandler(handler)

    return commands[namespace.command]()
