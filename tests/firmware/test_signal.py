import numpy as np
import pytest
from matplotlib import pyplot as plt

from lenlab.launchpad.protocol import pack


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
    send(packet := pack(b"ssinu"))  # create sinus
    reply = receive(8)
    assert reply == packet

    send(packet := pack(b"sharm"))  # add harmonic
    reply = receive(8)
    assert reply == packet

    # DAC output PA15
    send(packet := pack(b"sstar"))  # start
    reply = receive(8)
    assert reply == packet

    send(pack(b"sget?"))  # get data
    reply = receive(2 * 2000 + 8)
    payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)

    fig, ax = plt.subplots()
    ax.plot(payload)
    ax.grid()
    fig.show()


def test_osci(firmware, send, receive):
    send(packet := pack(b"orun!"))  # run
    reply = receive(8)
    assert reply == packet

    # ch1 input AP24
    send(pack(b"och1?"))  # get data
    reply = receive(8 + 4 * 3 * 1024)
    payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)

    fig, ax = plt.subplots()
    ax.plot(payload)
    ax.grid()
    fig.show()
