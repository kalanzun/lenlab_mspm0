from .app import App

from .window import MainWindow
from ..launchpad.discovery import Discovery


def main():
    app = App.get_instance()

    discovery = Discovery()
    discovery.available.connect(discovery.probe)

    window = MainWindow(discovery)
    window.show()

    discovery.find()

    app.exec()
