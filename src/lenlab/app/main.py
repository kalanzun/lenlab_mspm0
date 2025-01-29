import logging
from importlib import metadata

from ..controller.lenlab import Lenlab
from ..controller.report import Report
from .app import App
from .window import MainWindow

logger = logging.getLogger(__name__)


def main():
    app = App()
    logging.basicConfig(level=logging.NOTSET)

    lenlab = Lenlab()
    report = Report()

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    window = MainWindow(lenlab, report)
    window.show()

    app.exec()
