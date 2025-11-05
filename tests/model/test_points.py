import numpy as np
import pytest

from lenlab.launchpad.protocol import pack
from lenlab.model.points import Points


@pytest.fixture
def reply():
    payload = np.empty((2 * 4096,), np.dtype("<u2"))
    payload[::2] = np.arange(0, 4096)  # channel 1
    payload[1::2] = 4096 - payload[::2]  # channel 2

    interval_25ns = 1000 * 40_000
    return pack(b"v", arg=interval_25ns.to_bytes(4, "little"), length=4096) + payload.tobytes()


def test_parse_reply(reply):
    points = Points()
    points.parse_reply(reply)

    rising = np.linspace(0, 3.3, 4096, endpoint=False)
    falling = np.linspace(3.3, 0, 4096, endpoint=False)

    assert points.get_seconds()[-1] == 4095.0
    assert np.allclose(points.get_seconds(), np.linspace(0, 4096, 4096, endpoint=False))
    assert np.allclose(points.get_channel(0), rising)
    assert np.allclose(points.get_channel(1), falling)

    points.parse_reply(reply)

    assert points.get_seconds()[-1] == 8191.0
    assert np.allclose(points.get_channel(0)[:4096], rising)
    assert np.allclose(points.get_channel(1)[:4096], falling)
    assert np.allclose(points.get_channel(0)[4096:], rising)
    assert np.allclose(points.get_channel(1)[4096:], falling)


def test_numpy_mean():
    data = np.asarray([0, 0, 1, 1, 2, 2, 3, 3])
    data = data.reshape((4, 2))
    data = data.mean(axis=1)
    assert np.allclose(data, np.asarray([0, 1, 2, 3]))
