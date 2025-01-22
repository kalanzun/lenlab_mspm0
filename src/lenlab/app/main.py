from importlib import metadata
from io import StringIO
from logging import NOTSET, StreamHandler, basicConfig, getLogger

from ..launchpad.discovery import Discovery
from .app import App
from .window import MainWindow

logger = getLogger(__name__)


def main():
    app = App()

    basicConfig(level=NOTSET)
    error_report = StringIO()
    handler = StreamHandler(error_report)
    getLogger().addHandler(handler)

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    discovery = Discovery()
    discovery.available.connect(discovery.probe)

    window = MainWindow(error_report, discovery)
    window.show()

    discovery.find()

    app.exec()
