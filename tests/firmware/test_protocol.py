import logging
from time import sleep

import numpy as np
import pytest
from matplotlib import pyplot as plt
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad.protocol import command

logger = logging.getLogger(__name__)

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
knock_packet = b"Lk\x08\x00nock, knock!"
knock_reply = b"Lk\x00\x00nock"


@pytest.fixture(scope="module")
def send(port):
    def send(cmd: bytes):
        port.write(cmd)

    return send


@pytest.fixture(scope="module")
def receive(port):
    def receive(n: int, timeout: int = 400) -> bytes:
        while port.bytesAvailable() < n:
            if not port.waitForReadyRead(timeout):
                raise TimeoutError(f"{port.bytesAvailable()} bytes of {n} bytes received")
        return port.read(n).data()

    return receive


def test_bsl_resilience_to_false_baud_rate(bsl, port: QSerialPort):
    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert not port.waitForReadyRead(400), "BSL should not reply"

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert port.waitForReadyRead(400), "BSL should reply"

    # assume cold BSL
    # warm BSL for further tests
    reply = port.readAll().data()
    assert reply == b"\x00"


def test_firmware_resilience_to_false_baud_rate(firmware, port: QSerialPort):
    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)
    assert not port.waitForReadyRead(400), "Firmware should not reply"

    # send the knock packet at 1 MBaud
    port.setBaudRate(1_000_000)
    port.write(knock_packet)
    assert port.waitForReadyRead(400), "Firmware should reply"

    reply = port.readAll().data()
    assert reply == knock_reply


def test_knock(firmware, send, receive):
    send(knock_packet)
    reply = receive(len(knock_reply))
    assert reply == knock_reply


@pytest.fixture(scope="module")
def get_sinus(send, receive):
    def get_sinus(length: int, amplitude: int, multiplier: int = 0, harmonic: int = 0):
        # MATHACL sine produces an error at exactly -90 deg if length is 512 or 1024
        # current firmware has a workaround
        send(command(b"s", 0, length, amplitude, multiplier, harmonic))

        reply = receive(8 + 2 * 2000)  # 8 byte header + 2000 * int16_t
        payload = np.frombuffer(reply, np.dtype("<i2"), offset=8)
        assert int.from_bytes(reply[2:4], byteorder="little") == 2 * 2000
        assert int.from_bytes(reply[4:8], byteorder="little") == length
        return payload[:length]

    return get_sinus


def time(length: int, multiplier: int = 1) -> np.ndarray:
    return np.linspace(0, 2 * np.pi * multiplier, endpoint=False, num=length)


def expected_sinus(length: int, amplitude: int, multiplier: int = 0, harmonic: int = 0):
    expected = np.sin(time(length)) * amplitude + np.sin(time(length, multiplier)) * harmonic
    return np.round(expected).astype("<i2")


def plot(title, *waveforms):
    fig, ax = plt.subplots()
    for waveform in waveforms:
        ax.plot(waveform)
    ax.set_title(title)
    ax.grid()
    fig.show()


def check_sinus(sinus: np.ndarray, expected: np.ndarray, title: str):
    error = np.absolute(expected - sinus)
    if not np.all(error < 4):
        max_error = int(error.max())
        error_count = int(np.count_nonzero(error == max_error))
        logger.info(f"{title}, {max_error=}, {error_count=}")

        if not (max_error < 8 and error_count <= 4):
            plot(f"{title}, {max_error=}, {error_count=}", sinus, expected)

        assert max_error < 8 and error_count <= 4


# @pytest.mark.parametrize("length", list(range(200, 2002, 2)))  # 70 seconds
@pytest.mark.parametrize(
    "length", [200, 202, 220, 500, 512, 800, 802, 998, 1000, 1002, 1022, 1024, 1026, 1998, 2000]
)
def test_sinus(firmware, get_sinus, length):
    # DAC output PA15

    amplitude = 2000
    sinus = get_sinus(length, amplitude)
    expected = expected_sinus(length, amplitude)

    check_sinus(sinus, expected, f"sinus {length=}")


@pytest.mark.parametrize(
    "length", [200, 202, 220, 500, 512, 800, 802, 998, 1000, 1002, 1022, 1024, 1026, 1998, 2000]
)
@pytest.mark.parametrize("multiplier", [2, 3, 4, 5, 8, 10, 15, 18, 19, 20])
def test_harmonic(firmware, get_sinus, length, multiplier):
    # DAC output PA15

    amplitude = 1000
    sinus = get_sinus(length, amplitude, multiplier, amplitude)
    expected = expected_sinus(length, amplitude, multiplier, amplitude)

    check_sinus(sinus, expected, f"sinus {length=}, {multiplier=}")


def test_oscilloscope(firmware, output, send, receive):
    # ch1 input PA24
    # ch2 input PA17

    # sample rate 1 MHz
    # DAC 1 kHz
    # interval 40 in 25 ns
    send(command(b"a", 40, 1000, int(4096 / 3.3), 0, 0))  # run
    payload_size = 4 * 2 * 8 * 432
    reply = receive(8 + payload_size)
    length = int.from_bytes(reply[2:4], byteorder="little")
    assert length == payload_size

    channels = np.frombuffer(reply, np.dtype("<u2"), offset=8)
    mid = channels.shape[0] // 2
    ch1 = channels[:mid]
    ch2 = channels[mid:]

    fig, ax = plt.subplots()
    ax.plot(ch1)
    ax.plot(ch2)
    ax.set_title("oscilloscope acquire")
    ax.grid()
    fig.savefig(output / "oscilloscope.svg")


def test_voltmeter(firmware, send, receive):
    # ch1 input PA24
    # ch2 input PA17

    # sample interval 200 ms
    # interval 8000000 in 25 ns
    send(command(b"v", 8000000))  # start logging 200 ms
    reply = receive(8)
    assert reply == b"Lv\x00\x00\x00\x12z\x00"

    sleep(1)

    send(command(b"x", 0))  # get points and stop logging
    reply = receive(8)
    assert reply.startswith(b"Lx")
    length = int.from_bytes(reply[2:4], byteorder="little")
    assert length == 20
    arg = int.from_bytes(reply[4:8], byteorder="little")
    assert arg == 0

    payload = receive(length)
    assert payload
