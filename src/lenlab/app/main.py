import argparse
import logging
from importlib import metadata

from ..controller.lenlab import Lenlab
from ..controller.report import Report
from .app import App
from .window import MainWindow

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    app = App()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--port",
        help="Launchpad port to connect to (skips discovery)",
    )
    parser.add_argument(
        "--probe-timeout",
        default=600,
        type=int,
        help="timeout for probing in milliseconds, default %(default)s",
    )
    parser.add_argument(
        "--reply-timeout",
        default=600,
        type=int,
        help="timeout for firmware replies in milliseconds, default %(default)s",
    )

    args = parser.parse_args(argv)

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    lenlab = Lenlab(args.port, args.probe_timeout, args.reply_timeout)
    report = Report()

    window = MainWindow(lenlab, report)
    window.show()

    app.exec()
