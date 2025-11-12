import numpy as np
import pytest

from lenlab.launchpad.protocol import pack
from lenlab.model.points import Points


@pytest.fixture
def length():
    return 1024


@pytest.fixture
def reply(length):
    amplitude = 4
    assert length * amplitude == 4096

    payload = np.empty((2 * length,), np.dtype("<u2"))
    payload[::2] = np.arange(0, length) * amplitude  # channel 1
    payload[1::2] = 4095 - payload[::2]  # channel 2

    interval_25ns = 1000 * 40_000  # 1 s
    return pack(b"v", arg=interval_25ns.to_bytes(4, "little"), length=length) + payload.tobytes()


@pytest.fixture
def rising(length):
    stop = 3.3 / 4095 * 4092
    return np.linspace(0, stop, length, endpoint=True)


@pytest.fixture
def falling(length):
    stop = 3.3 / 4095 * 3
    return np.linspace(3.3, stop, length, endpoint=True)


def test_parse_reply(length, reply, rising, falling):
    points = Points(0.1)
    points.parse_reply(reply)

    current_time = (length - 1) * points.interval
    assert points.get_last_time() == current_time
    assert round(points.get_last_value(0), 2) == 3.3
    assert round(points.get_last_value(1), 2) == 0.0

    chart = points.create_chart()
    assert np.allclose(chart.channels[0], rising)
    assert np.allclose(chart.channels[1], falling)


def test_append_reply(length, reply, rising, falling):
    points = Points(1.0)
    points.parse_reply(reply)
    points.parse_reply(reply)

    current_time = 2 * length * points.interval - 1.0
    # still under two hours
    assert current_time < 2 * 60 * 60
    assert points.get_last_time() == current_time
    assert round(points.get_last_value(0), 2) == 3.3
    assert round(points.get_last_value(1), 2) == 0.0

    chart = points.create_chart()
    assert np.allclose(chart.channels[0][:length], rising)
    assert np.allclose(chart.channels[1][:length], falling)
    assert np.allclose(chart.channels[0][length:], rising)
    assert np.allclose(chart.channels[1][length:], falling)


def test_numpy_mean():
    data = np.asarray([0, 0, 1, 1, 2, 2, 3, 3])
    data = data.reshape((4, 2))
    data = data.mean(axis=1)
    assert np.allclose(data, np.asarray([0, 1, 2, 3]))


def test_numpy_mean_two_channels():
    data = np.asarray([0, 5, 0, 5, 1, 6, 1, 6, 2, 7, 2, 7, 3, 8, 3, 8])
    data = data.reshape((8, 2))

    data = data.reshape((4, 2, 2))
    data = data.mean(axis=1)
    assert np.allclose(data, np.asarray([[0, 5], [1, 6], [2, 7], [3, 8]]))


def test_numpy_pad():
    data = np.empty((4,))
    data = np.pad(data, (0, 4), mode="empty")
    assert data.shape == (8,)


def test_numpy_pad_two_channels():
    data = np.empty((4, 2))
    data = np.pad(data, ((0, 4), (0, 0)), mode="empty")
    assert data.shape == (8, 2)


def test_numpy_cast():
    payload = np.asarray([1, 2], np.dtype("<u2"))
    values = payload / 2
    assert values.dtype == np.double
    assert np.allclose(values, np.asarray([0.5, 1.0]))


def test_compression(length, reply):
    points = Points(interval=0.2)

    # one reply is 1024 points (interval = 0.2 seconds) or 3.4 minutes
    points.parse_reply(reply)

    # it should batch to seconds after two minutes
    chart = points.create_chart()
    compressed = int(length * points.interval)
    assert chart.x.shape == (compressed,)
    assert chart.channels[0].shape == (compressed,)
    assert chart.channels[1].shape == (compressed,)


def test_padding(length, reply):
    points = Points(interval=1.0)

    for _ in range(100):
        points.parse_reply(reply)

    assert points.channels[0].shape == (110_000,)
    assert points.channels[1].shape == (110_000,)


def test_huge_compression(length, reply):
    points = Points(interval=0.1)

    # one reply is 1024 points (interval = 0.1 seconds)
    # one hundred replies is 2.84 hours
    for _ in range(100):
        points.parse_reply(reply)

    # it should batch to minutes after two hours
    chart = points.create_chart()
    compressed = int(100 * length * points.interval) // 60
    assert chart.x.shape == (compressed,)
    assert chart.channels[0].shape == (compressed,)
    assert chart.channels[1].shape == (compressed,)
