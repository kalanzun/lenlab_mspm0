import pytest

from lenlab.app.poster import PosterWidget
from lenlab.message import Message


class NoShowPosterWidget(PosterWidget):
    def show(self):
        pass


@pytest.fixture()
def poster(qt_widgets):
    return NoShowPosterWidget()


def test_set_success(poster):
    poster.set_success(Message())


def test_set_error(poster):
    poster.set_error(Message())
