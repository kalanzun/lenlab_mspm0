import pytest

from lenlab.app.programmer import ProgrammerWidget
from lenlab.controller.programmer import ProgrammingSuccessful
from lenlab.launchpad.discovery import Discovery
from lenlab.spy import Spy


@pytest.fixture()
def discovery():
    return Discovery()


@pytest.fixture()
def programmer(qt_widgets, discovery):
    return ProgrammerWidget(discovery)


def test_program(programmer):
    spy = Spy(programmer.programmer.error)
    programmer.on_program_clicked()
    assert spy.count() == 1


def test_success(programmer):
    programmer.programmer.success.emit(ProgrammingSuccessful())


def test_export(programmer, save_file):
    programmer.on_export_clicked()

    content = save_file.read_bytes()
    assert len(content) > 0


def test_no_file(programmer, save_file):
    save_file.cancel = True
    programmer.on_export_clicked()
