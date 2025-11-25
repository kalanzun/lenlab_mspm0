import numpy as np
import pytest

from lenlab.app.bode import BodeWidget
from lenlab.controller.signal import sine_table
from lenlab.model.waveform import Waveform


@pytest.fixture()
def bode(qt_widgets, lenlab):
    return BodeWidget(lenlab)


@pytest.fixture()
def waveform():
    channel_length = 8 * 864

    channels = [
        np.sin(np.linspace(0, 4 * np.pi, channel_length, endpoint=False)),
        np.cos(np.linspace(0, 4 * np.pi, channel_length, endpoint=False)),
    ]
    return Waveform(channel_length, 0, 1e-6, channels)


def test_ready(lenlab, bode):
    lenlab.ready.emit(True)


def test_start(bode, terminal):
    bode.on_start_clicked()
    assert bode.bode.active is True

    command = terminal.get_single_command()
    assert command.startswith(b"Lb")


def test_stop(bode, terminal):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.stop()
    assert bode.bode.active is False


def test_reply(bode, terminal, waveform):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.on_bode(waveform)
    rows = list(bode.bode.rows())
    assert len(rows) == 1


def test_finish(bode, terminal, waveform):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.index = len(sine_table) - 1
    bode.bode.on_bode(waveform)
    assert bode.bode.active is False


def test_save_as(bode, terminal, waveform, save_as_output):
    bode.on_start_clicked()
    assert bode.bode.active is True

    bode.bode.index = len(sine_table) - 1
    bode.bode.on_bode(waveform)

    bode.on_save_as_clicked()
    content = save_as_output["file_path"].read_text(encoding="utf-8")
    assert content.startswith("Lenlab_MSPM0,8.6,bode_plot\nfrequency,magnitude,phase\n10000")
