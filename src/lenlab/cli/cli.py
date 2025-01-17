import logging
import sys
from argparse import ArgumentParser
from importlib import metadata

from lenlab.app.window import MainWindow

logger = logging.getLogger(__name__)

commands = {}


def command(func):
    commands[func.__name__] = func
    return func


@command
def app(args):
    from lenlab.app.app import App

    app = App.get_instance()

    window = MainWindow()
    window.show()

    return app.exec()


@command
def blank(args):
    pass


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

    parser.add_argument(
        "--port",
        nargs="?",
    )

    args = parser.parse_args()
    if args.log:
        handler = logging.FileHandler(args.log, mode="w", encoding="utf-8")
        logging.getLogger().addHandler(handler)

    try:
        version = metadata.version("lenlab")
        logger.info(f"Lenlab {version}")
    except metadata.PackageNotFoundError:
        logger.info("Lenlab development version")

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
