import logging
from importlib import metadata

from lenlab.queued import QueuedCall

from ..controller.report import Report
from ..launchpad.discovery import Discovery
from .app import App
from .window import MainWindow

logger = logging.getLogger(__name__)


def main():
    app = App()
    logging.basicConfig(level=logging.NOTSET)

    report = Report()

    discovery = Discovery()
    QueuedCall(discovery, discovery.find)

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    window = MainWindow(report, discovery)
    window.show()

    app.exec()
