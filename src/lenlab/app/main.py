import argparse
import logging
import signal
import sys
from importlib import metadata
from traceback import format_exception, format_exception_only

from attrs import frozen
from PySide6.QtCore import (
    QLibraryInfo,
    QLocale,
    QSysInfo,
    QTimer,
    QTranslator,
)
from PySide6.QtWidgets import QApplication, QMessageBox

from ..controller.lenlab import Lenlab
from ..controller.report import Report
from ..language import Language
from ..message import Message
from ..queued import QueuedCall
from ..translate import tr
from .window import MainWindow

logger = logging.getLogger(__name__)


@frozen
class ExceptionHandler:
    window: MainWindow

    def install(self):
        sys.excepthook = self
        return self

    def __call__(self, exc, value, tb):
        text = "".join(format_exception_only(exc, value)).strip()
        details = "".join(format_exception(exc, value, tb)).strip()

        logger.error(details)

        msg = QMessageBox(self.window)
        msg.setWindowTitle(tr("Error", "Fehler"))
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(text)
        msg.setInformativeText(ErrorReport().one_line())
        msg.setDetailedText(details)
        msg.addButton(QMessageBox.StandardButton.Ok)
        msg.show()


class ErrorReport(Message):
    english = """An error occurred. If you want to ask about it or report it,
    please attach the error report from the main menu (Lenlab -> Save error report).
    The error report contains the error information and some context.
    """
    german = """Ein Fehler ist aufgetreten.
    Wenn Sie nachfragen oder den Fehler berichten möchten, schicken Sie bitten den Fehlerbericht
    aus dem Hauptmenü mit (Lenlab -> Fehlerbericht speichern).
    Der Fehlerbericht enthält die Fehlerinformationen und etwas Kontext.  
    """


@frozen
class InterruptHandler:
    window: MainWindow

    def install(self):
        # Keyboard interrupt handler
        signal.signal(signal.SIGINT, self)

        # Python processes the interrupt signal only when Qt calls into Python
        poll = QTimer(self.window)
        poll.timeout.connect(lambda: None)
        poll.start(100)

        return self

    def __call__(self, num, frame):
        logger.info("keyboard interrupt")
        QueuedCall(self.window, self.window.close)


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

    # Exception Handler
    ExceptionHandler(window).install()

    # Keyboard interrupt handler
    InterruptHandler(window).install()

    app.exec()
