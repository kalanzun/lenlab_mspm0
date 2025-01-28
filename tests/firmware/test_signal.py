import numpy as np
import pytest
from matplotlib import pyplot as plt

from lenlab.launchpad.protocol import command, pack


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


def test_sinus(firmware, send, receive):
    # DAC output PA15
    length = 1024  # my board produces a calculation error
    length = 512  # my board produces a calculation error
    send(command(b"s", 1000, length, 1024, 0, 256))
    reply = receive(8)
    assert reply == pack(b"s")

    send(command(b"g"))
    reply = receive(2 * 2000 + 8)
    payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)

    fig, ax = plt.subplots()
    ax.plot(payload[:length])
    ax.grid()
    fig.show()


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
