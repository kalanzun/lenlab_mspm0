import logging
from importlib import metadata

from ..controller.report import Report
from .app import App
from .window import MainWindow

logger = logging.getLogger(__name__)


def main():
    app = App()
    logging.basicConfig(level=logging.NOTSET)

    report = Report()

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    window = MainWindow(report)
    window.show()

    app.exec()
