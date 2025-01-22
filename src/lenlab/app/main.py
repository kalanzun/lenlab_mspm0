from ..launchpad.discovery import Discovery
from .app import App
from .window import MainWindow


def main():
    app = App()

    discovery = Discovery()
    discovery.available.connect(discovery.probe)

    window = MainWindow(discovery)
    window.show()

    discovery.find()

    app.exec()
