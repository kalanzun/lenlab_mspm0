import numpy as np
import pytest
from matplotlib import pyplot as plt

from lenlab.launchpad.protocol import command


@pytest.fixture(scope="module")
def send(port):
    def send(command: bytes):
        port.write(command)

    return send


@pytest.fixture(scope="module")
def receive(port):
    def receive(n: int, timeout: int = 400) -> bytes:
        while port.bytesAvailable() < n:
            if not port.waitForReadyRead(timeout):
                raise TimeoutError(f"{port.bytesAvailable()} bytes of {n} bytes received")
        return port.read(n).data()

    return receive


# 44 seconds
@pytest.mark.parametrize("length", list(range(800, 2002, 2)))
def test_sinus(firmware, send, receive, length):
    # DAC output PA15

    amplitude = 2000
    # MATHACL produces an error at exactly -90 deg
    # length = 1024
    # length = 512
    send(command(b"s", 0, length, amplitude, 0, 256))

    reply = receive(2 * 2000 + 8)
    payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)
    sinus = payload[:length]

    expected = np.sin(np.linspace(0, 2 * np.pi, endpoint=False, num=length)) * amplitude
    expected = expected.astype("<i2")

    # fig, ax = plt.subplots()
    # ax.plot(sinus)
    # ax.plot(expected)
    # ax.grid()
    # fig.show()

    assert np.all(np.absolute(expected - sinus) < 4)


def test_osci(firmware, send, receive):
    # ch1 input PA24
    # ch2 input PA17
    send(command(b"a", 5))  # run
    reply = receive(8 + 2 * 4 * 3 * 1024)
    channels = np.frombuffer(reply, np.dtype("<i2"), offset=8)
    mid = channels.shape[0] // 2
    ch1 = channels[:mid]
    ch2 = channels[mid:]

    fig, ax = plt.subplots()
    ax.plot(ch1)
    ax.plot(ch2)
    ax.grid()
    fig.show()
