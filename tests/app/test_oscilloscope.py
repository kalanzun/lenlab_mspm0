import pytest

from lenlab.app.oscilloscope import OscilloscopeWidget
from lenlab.controller.lenlab import Lenlab
from lenlab.controller.oscilloscope import example_reply
from lenlab.spy import Spy


@pytest.fixture()
def lenlab():
    lenlab = Lenlab()
    return lenlab


@pytest.fixture()
def spy(lenlab):
    lenlab.lock.release()
    lenlab.adc_lock.release()
    return Spy(lenlab.terminal_write)


@pytest.fixture()
def oscilloscope(qt_widgets, lenlab):
    return OscilloscopeWidget(lenlab)


def test_acquire(spy, oscilloscope):
    assert oscilloscope.acquire()

    command = spy.get_single_arg()
    assert command.startswith(b"La")


def test_locked(oscilloscope):
    assert not oscilloscope.acquire()


def test_start(spy, oscilloscope):
    oscilloscope.on_start_clicked()

    command = spy.get_single_arg()
    assert command.startswith(b"La")
    assert oscilloscope.active


def test_stop(spy, oscilloscope):
    oscilloscope.on_start_clicked()
    oscilloscope.on_stop_clicked()

    assert not oscilloscope.active


def test_single(spy, oscilloscope):
    oscilloscope.on_single_clicked()

    command = spy.get_single_arg()
    assert command.startswith(b"La")
    assert not oscilloscope.active


def test_save_as(oscilloscope, mock_path):
    oscilloscope.on_save_as_clicked(file_path=mock_path)

    assert mock_path.get_line_count() == 2


def test_reply(lenlab, spy, oscilloscope):
    assert oscilloscope.acquire()

    command = spy.get_single_arg()
    assert command.startswith(b"La")
    assert lenlab.adc_lock.is_locked

    oscilloscope.on_reply(example_reply())
    assert not lenlab.adc_lock.is_locked


def test_reply_filter(lenlab, spy, oscilloscope):
    oscilloscope.on_reply(b"Lk\x00\x00nock")


def test_restart(lenlab, spy, oscilloscope):
    oscilloscope.on_start_clicked()
    assert oscilloscope.active

    command = spy.get_single_arg()
    assert command.startswith(b"La")

    # the reply bypasses lenlab, release the lock manually
    lenlab.lock.release()
    oscilloscope.on_reply(example_reply())

    assert oscilloscope.active

    assert spy.count() == 2
    command = spy.at(1)[0]
    assert command.startswith(b"La")


def test_bode(oscilloscope):
    spy = Spy(oscilloscope.bode)
    oscilloscope.on_reply(example_reply(b"b"))

    waveform = spy.get_single_arg()
    assert waveform
