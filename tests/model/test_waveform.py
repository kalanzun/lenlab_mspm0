from io import StringIO

import numpy as np
import pytest

from lenlab.launchpad.protocol import pack
from lenlab.model.waveform import Waveform

channel_length = 8 * 864


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


@pytest.fixture
def waveform(reply):
    return Waveform.parse_reply(reply)


def test_parse_reply(waveform):
    assert waveform.length == channel_length
    assert waveform.offset == 88
    assert waveform.time_step == 1e-6


def test_time_aligned(waveform):
    time = waveform.time_aligned()
    assert time.shape == (6001,)
    assert time[0] == -3e-3
    assert time[-1] == 3e-3


@pytest.mark.parametrize("index", [0, 1])
def test_channel_aligned(waveform, index):
    channel = waveform.channel_aligned(index)
    assert channel.shape == (6001,)

    value_0 = int(round((float(channel[0]) + 1.65) / 3.3 * 4096))
    assert value_0 == 88


def test_save_as(waveform):
    file = StringIO()
    waveform.save_as(file)
    assert len(file.getvalue().splitlines()) == 2 + 6001
