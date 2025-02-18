import argparse
import logging
import sys
from importlib import metadata

from PySide6.QtCore import QLibraryInfo, QLocale, QSysInfo, QTranslator
from PySide6.QtWidgets import QApplication

from ..controller.lenlab import Lenlab
from ..controller.report import Report
from ..language import Language
from .window import MainWindow

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    app = QApplication()

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--port",
        help="Launchpad port to connect to (skips discovery)",
    )
    parser.add_argument(
        "--probe-timeout",
        default=Lenlab.default_probe_timeout,
        type=int,
        help="timeout for probing in milliseconds, default %(default)s",
    )
    parser.add_argument(
        "--reply-timeout",
        default=Lenlab.default_reply_timeout,
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

    # Qt translations
    path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator = QTranslator(app)
    if translator.load(QLocale(), "qtbase", "_", path):
        app.installTranslator(translator)

    # Message translations
    if QLocale().language() == QLocale.Language.German:
        Language.language = "german"

    window = MainWindow(lenlab, report, rules=sys.platform == "linux")
    window.show()

    app.exec()
