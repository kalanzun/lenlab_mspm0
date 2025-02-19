import numpy as np
import pytest
from PySide6.QtWidgets import QFileDialog

from lenlab.app.oscilloscope import OscilloscopeWidget
from lenlab.controller.lenlab import Lenlab
from lenlab.launchpad.protocol import pack
from lenlab.spy import Spy

channel_length = 8 * 864


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
def oscilloscope(widgets, lenlab):
    return OscilloscopeWidget(lenlab)


def test_acquire(spy, oscilloscope):
    assert oscilloscope.acquire()

    command = spy.get_single_arg()
    assert command.startswith(b"La")


def test_locked(lenlab, oscilloscope):
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


class SaveFile:
    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        self.cancel = False

    def __call__(self, parent, title, file_name, file_format):
        if self.cancel:
            return "", ""

        self.tmp_file = self.tmp_path / file_name
        return str(self.tmp_file), file_format

    def read_text(self):
        return self.tmp_file.read_text(encoding="utf-8")


@pytest.fixture()
def save_file(monkeypatch, tmp_path):
    save_file = SaveFile(tmp_path)
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        save_file,
    )
    return save_file


def test_save_as(oscilloscope, save_file):
    oscilloscope.on_save_as_clicked()

    content = save_file.read_text()
    assert len(content) > 0


def test_no_file(oscilloscope, save_file):
    save_file.cancel = True
    oscilloscope.on_save_as_clicked()


@pytest.fixture
def reply():
    sampling_interval_25ns = 40  # 1 MHz
    # sine_samples = 4000  # 250 kHz
    offset = 88

    arg = sampling_interval_25ns.to_bytes(2, "little") + offset.to_bytes(2, "little")
    channel_1 = channel_2 = np.linspace(
        0, channel_length, channel_length, dtype=np.dtype("<u2")
    ).tobytes()

    return pack(b"a", arg, 2 * channel_length) + channel_1 + channel_2


def test_reply(lenlab, spy, oscilloscope, reply):
    assert oscilloscope.acquire()

    command = spy.get_single_arg()
    assert command.startswith(b"La")
    assert lenlab.adc_lock.is_locked

    oscilloscope.on_reply(reply)
    assert not lenlab.adc_lock.is_locked


def test_reply_filter(lenlab, spy, oscilloscope):
    oscilloscope.on_reply(b"Lk\x00\x00nock")


def test_restart(lenlab, spy, oscilloscope, reply):
    oscilloscope.on_start_clicked()
    assert oscilloscope.active

    command = spy.get_single_arg()
    assert command.startswith(b"La")

    # the reply bypasses lenlab, release the lock manually
    lenlab.lock.release()
    oscilloscope.on_reply(reply)

    assert oscilloscope.active

    assert spy.count() == 2
    command = spy.at(1)[0]
    assert command.startswith(b"La")


def test_bode(oscilloscope, reply):
    spy = Spy(oscilloscope.bode)
    reply = b"Lb" + reply[2:]
    oscilloscope.on_reply(reply)

    waveform = spy.get_single_arg()
    assert waveform
