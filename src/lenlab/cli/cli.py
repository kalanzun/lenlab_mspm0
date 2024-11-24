import logging
import signal
import sys
from argparse import ArgumentParser
from importlib import metadata

from PySide6.QtCore import QCoreApplication, QLocale
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

commands = {}


def command(func):
    commands[func.__name__] = func
    return func


@command
def app():
    from lenlab.app.window import MainWindow
    from lenlab.message import Message

    gui_app = QApplication(sys.argv)

    if QLocale().language() == QLocale.Language.German:
        Message.language = "german"

    window = MainWindow()
    window.show()

    return gui_app.exec()


@command
def sys_info():
    from lenlab.cli.sys_info import sys_info

    sys_info()
    return 0


@command
def profile():
    from lenlab.cli.profile import profile

    cli_app = QCoreApplication()
    signal.signal(signal.SIGINT, lambda signum, frame: cli_app.exit(130))
    # the signal will stop any local event loops, too
    profile()
    return 0


@command
def flash():
    from lenlab.cli.flash import flash

    cli_app = QCoreApplication()
    signal.signal(signal.SIGINT, lambda signum, frame: cli_app.exit(130))
    # the signal will stop any local event loops, too
    flash()
    return 0


@command
def exercise():
    from lenlab.cli.exercise import exercise

    cli_app = QCoreApplication()
    signal.signal(signal.SIGINT, lambda signum, frame: cli_app.exit(130))
    # the signal will stop any local event loops, too
    exercise()
    return 0


def main():
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

    logging.basicConfig(level=logging.INFO)

    options = parser.parse_args()
    if options.log:
        handler = logging.FileHandler(options.log, mode="w", encoding="utf-8")
        logging.getLogger().addHandler(handler)

    try:
        version = metadata.version("lenlab")
        logger.info(f"Lenlab {version}")
    except metadata.PackageNotFoundError:
        logger.info("Lenlab development version")

    return commands[options.command]()


if __name__ == "__main__":
    sys.exit(main())
