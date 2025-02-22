import numpy as np
import pytest

from lenlab.app.bode import BodeWidget
from lenlab.controller.lenlab import Lenlab
from lenlab.controller.oscilloscope import channel_length
from lenlab.controller.signal import sine_table
from lenlab.model.waveform import Waveform
from lenlab.spy import Spy


@pytest.fixture()
def lenlab():
    lenlab = Lenlab()
    return lenlab


@pytest.fixture()
def unlocked(lenlab):
    lenlab.lock.release()
    lenlab.adc_lock.release()
    return lenlab


@pytest.fixture()
def spy(unlocked):
    return Spy(unlocked.terminal_write)


@pytest.fixture()
def bode(qt_widgets, lenlab):
    return BodeWidget(lenlab)


@pytest.fixture()
def waveform():
    channels = (
        np.sin(np.linspace(0, 2 * np.pi, channel_length, endpoint=False)),
        np.cos(np.linspace(0, 2 * np.pi, channel_length, endpoint=False)),
    )
    return Waveform(channel_length, 0, 1e-6, channels)


def test_ready(lenlab, bode):
    lenlab.ready.emit(True)


def test_start(spy, bode):
    bode.on_start_clicked()
    assert bode.bode.active is True

    command = spy.get_single_arg()
    assert command.startswith(b"Lb")


def test_active(bode):
    bode.bode.active = True
    bode.on_start_clicked()


def test_locked(bode):
    bode.on_start_clicked()


def test_stop(unlocked, bode):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.stop()
    assert bode.bode.active is False


def test_reply(unlocked, bode, waveform):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.on_bode(waveform)


def test_save_as(unlocked, bode, save_file, waveform):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.on_bode(waveform)

    bode.on_save_as_clicked()

    content = save_file.read_text()
    assert len(content) > 0


def test_finish(spy, bode, save_file, waveform):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.index = len(sine_table) - 1
    bode.bode.on_bode(waveform)
