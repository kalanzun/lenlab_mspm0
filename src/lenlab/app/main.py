import argparse
import logging
import sys
from importlib import metadata

from PySide6.QtCore import QLibraryInfo, QSysInfo

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

    report = Report()

    logger.info(f"Lenlab {metadata.version('lenlab')}")
    logger.info(f"Python {sys.version}")
    logger.info(f"Python Virtual Environment {sys.prefix}")
    logger.info(f"PySide6 {metadata.version('PySide6')}")
    logger.info(f"Qt {QLibraryInfo.version().toString()}")
    logger.info(f"Architecture {QSysInfo.currentCpuArchitecture()}")
    logger.info(f"Kernel {QSysInfo.prettyProductName()}")

    lenlab = Lenlab(args.port, args.probe_timeout, args.reply_timeout)

    window = MainWindow(lenlab, report)
    window.show()

    app.exec()
