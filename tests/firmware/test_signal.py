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
    send(command(b"ssin!", 2000, 1024, 20, 256))
    reply = receive(8)
    assert reply == pack(b"ssin!")

    send(command(b"sdat?"))
    reply = receive(2 * 2000 + 8)
    payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)

    fig, ax = plt.subplots()
    ax.plot(payload)
    ax.grid()
    fig.show()


def test_osci(firmware, send, receive):
    send(command(b"oacq!", 1))  # run
    reply = receive(8)
    assert reply == pack(b"oacq!")

    # ch1 input PA24
    send(command(b"och1?"))  # get data
    reply = receive(8 + 4 * 3 * 1024)
    channel1 = np.frombuffer(reply, np.dtype("<i2"), offset=8)

    # ch2 input PA17
    send(command(b"och2?"))  # get data
    reply = receive(8 + 4 * 3 * 1024)
    channel2 = np.frombuffer(reply, np.dtype("<i2"), offset=8)

    fig, ax = plt.subplots()
    ax.plot(channel1)
    ax.plot(channel2)
    ax.grid()
    fig.show()
