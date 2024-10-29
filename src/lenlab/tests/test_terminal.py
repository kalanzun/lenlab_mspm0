from itertools import repeat

import numpy as np
import pytest

from lenlab.launchpad import KB, connect_packet, crc, ok_packet
from lenlab.lenlab import pack
from lenlab.terminal import Terminal
from lenlab.tests.spy import Spy


def test_bsl_connect(bsl, terminal: Terminal):
    spy = Spy(terminal.reply)
    ack = Spy(terminal.ack)
    terminal.write(connect_packet)
    reply = spy.run_until_single_arg()
    if reply is None:
        assert ack.get_single_arg() == b"\x00"
    else:
        assert reply == ok_packet


def test_knock(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"knock"))
    reply = spy.run_until_single_arg()
    assert reply == pack(b"knock")


def test_hitchhiker(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"knock") + b"knock")
    reply = spy.run_until_single_arg()
    assert reply == pack(b"knock")

    spy = Spy(terminal.reply)
    assert not spy.run_until()

    spy = Spy(terminal.reply)
    terminal.write(pack(b"knock"))
    reply = spy.run_until_single_arg()
    assert reply == pack(b"knock")


def test_command_too_short(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(b"Lk\x05\x00")
    assert not spy.run_until()

    spy = Spy(terminal.reply)
    terminal.write(pack(b"knock"))
    reply = spy.run_until_single_arg()
    assert reply == pack(b"knock")


@pytest.fixture(scope="module")
def memory(terminal: Terminal) -> np.ndarray:
    spy = Spy(terminal.reply)
    terminal.write(pack(b"mi28K"))  # init 28K
    reply = spy.run_until_single_arg(timeout=600)
    assert reply == pack(b"mi28K")

    return np.fromiter(crc(repeat(0, (28 * KB - 8) // 4), n_bits=32), dtype=np.dtype("<u4"))


# @pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, terminal: Terminal, memory: np.ndarray):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"mg28K"))  # get 28K
    reply = spy.run_until_single_arg(timeout=600)
    assert reply is not None, "no reply"

    head = reply[:8]
    assert head == b"Lm\xf8\x6fg28K", "invalid reply"

    # there seem to be no corrupt but complete packets
    size = len(reply)
    assert size == 28 * KB, "incomplete packet"

    # little endian, unsigned int, 4 byte, offset 8 bytes
    payload = np.frombuffer(reply, np.dtype("<u4"), offset=8)
    if not np.all(payload == memory):
        raise AssertionError("complete packet, but corrupt data")
