from importlib import metadata
from logging import NOTSET, StreamHandler, basicConfig, getLogger

from ..device.lenlab import Lenlab
from .app import App
from .window import MainWindow

logger = getLogger(__name__)


def main():
    app = App()

    lenlab = Lenlab()

    basicConfig(level=NOTSET)
    handler = StreamHandler(lenlab.error_report)
    getLogger().addHandler(handler)

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    window = MainWindow(lenlab)
    window.show()

    app.exec()
