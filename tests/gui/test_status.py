import pytest

from lenlab.app.status import BoardStatus
from lenlab.launchpad.discovery import Discovery
from lenlab.launchpad.terminal import Terminal
from lenlab.message import Message


@pytest.fixture()
def discovery():
    return Discovery()


@pytest.fixture()
def status(discovery):
    return BoardStatus(discovery)


def test_status(status):
    pass


def test_ready(status):
    status.on_ready(Terminal())


def test_error(status):
    status.on_error(Message())


def test_button(status):
    status.on_button_clicked()
