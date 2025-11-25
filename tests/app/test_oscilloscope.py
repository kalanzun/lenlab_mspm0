import numpy as np
import pytest

from lenlab.app.oscilloscope import OscilloscopeWidget
from lenlab.launchpad.protocol import pack
from lenlab.spy import Spy


@pytest.fixture()
def oscilloscope(qt_widgets, lenlab):
    return OscilloscopeWidget(lenlab)


def example_reply(code: bytes = b"a") -> bytes:
    channel_length = 8 * 864
    window = 6000

    sampling_interval_25ns = 40  # 1 MHz
    offset = (channel_length - window) // 2

    arg = sampling_interval_25ns.to_bytes(2, "little") + offset.to_bytes(2, "little")
    x = np.linspace(0, 4 * np.pi, channel_length, endpoint=False)
    channel_1 = (2047 * (np.sin(x) + 1.0)).astype(np.dtype("<u2")).tobytes()
    channel_2 = (2047 * (np.cos(x) + 1.0)).astype(np.dtype("<u2")).tobytes()

    return pack(code, arg, 2 * channel_length) + channel_1 + channel_2


def test_acquire(oscilloscope, terminal):
    assert oscilloscope.acquire()

    command = terminal.get_single_command()
    assert command.startswith(b"La")


def test_locked(oscilloscope):
    assert not oscilloscope.acquire()


def test_start(oscilloscope, terminal):
    oscilloscope.on_start_clicked()
    assert oscilloscope.active

    command = terminal.get_single_command()
    assert command.startswith(b"La")


def test_stop(oscilloscope, terminal):
    oscilloscope.on_start_clicked()
    oscilloscope.on_stop_clicked()

    assert not oscilloscope.active


def test_single(oscilloscope, terminal):
    oscilloscope.on_single_clicked()
    assert not oscilloscope.active

    command = terminal.get_single_command()
    assert command.startswith(b"La")


def test_reply(oscilloscope, lenlab, terminal):
    assert oscilloscope.acquire()
    assert lenlab.adc_lock.is_locked

    command = terminal.get_single_command()
    assert command.startswith(b"La")

    terminal.reply.emit(example_reply())
    assert not lenlab.adc_lock.is_locked


def test_reply_filter(oscilloscope, terminal):
    oscilloscope.on_reply(b"Lk\x00\x00nock")


def test_restart(oscilloscope, terminal):
    oscilloscope.on_start_clicked()
    assert oscilloscope.active

    command = terminal.get_single_command()
    assert command.startswith(b"La")

    terminal.reply.emit(example_reply())
    assert oscilloscope.active

    assert len(terminal.commands) == 2
    command = terminal.commands[1]
    assert command.startswith(b"La")


def test_bode(oscilloscope):
    spy = Spy(oscilloscope.bode)
    oscilloscope.on_reply(example_reply(b"b"))

    waveform = spy.get_single_arg()
    assert waveform


def test_save_as(oscilloscope, terminal, save_as_output):
    oscilloscope.on_single_clicked()
    terminal.reply.emit(example_reply())
    oscilloscope.on_save_as_clicked()
    content = save_as_output["file_path"].read_text(encoding="utf-8")
    assert content.startswith("Lenlab_MSPM0,8.6,oscilloscope\ntime,channel1,channel2\n-3.000")


def test_save_image(oscilloscope, terminal, save_as_output):
    oscilloscope.on_single_clicked()
    terminal.reply.emit(example_reply())
    oscilloscope.on_save_image_clicked()
    content = save_as_output["file_path"].read_text(encoding="utf-8")
    assert content.startswith(
        '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n'
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"'
    )
