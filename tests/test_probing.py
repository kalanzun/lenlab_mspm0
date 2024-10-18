import pytest

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy

from lenlab.terminal import SyncTerminal, Terminal, Probe


@pytest.fixture
def sync_terminal() -> SyncTerminal:
    sync_terminal = SyncTerminal()
    sync_terminal.open()

    yield sync_terminal

    sync_terminal.close()


def test_sync_probe(sync_terminal: SyncTerminal) -> None:
    if sync_terminal.is_open:
        assert sync_terminal.probe()


@pytest.fixture
def terminal() -> Terminal:
    terminal = Terminal()
    terminal.open()

    yield terminal

    terminal.close()


def test_probe(app: QCoreApplication, terminal: Terminal) -> None:
    if terminal.is_open:
        probe = Probe(terminal)
        probe.ready.connect(app.quit)
        ready = QSignalSpy(probe.ready)
        probe.error.connect(app.quit)
        error = QSignalSpy(probe.error)
        probe.start()
        app.exec()
        assert error.count() == 0
        assert ready.count() == 1
