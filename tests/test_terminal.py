import numpy as np
import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab.memory import check_memory, memory_28k
from lenlab.protocol import pack
from lenlab.spy import Spy
from lenlab.terminal import Terminal


@pytest.fixture(scope="module")
def terminal(port: QSerialPort) -> Terminal:
    terminal = Terminal(port)
    # port is already open
    # open() also connects the signal handlers
    terminal.open()
    yield terminal
    terminal.close()


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

    return memory_28k()


# @pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, terminal: Terminal, memory: np.ndarray):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"mg28K"))  # get 28K
    reply = spy.run_until_single_arg(timeout=600)
    assert reply is not None
    check_memory(b"mg28K", memory, reply)

    # 2024-11-05 four errors out of 8000 packets
    # FAILED src/lenlab/tests/test_terminal.py::test_28k[2480-8000] - AssertionError: no reply
    # FAILED src/lenlab/tests/test_terminal.py::test_28k[2481-8000] - AssertionError: no reply
    # FAILED src/lenlab/tests/test_terminal.py::test_28k[2493-8000] - AssertionError: no reply
    # FAILED src/lenlab/tests/test_terminal.py::test_28k[2494-8000] - AssertionError: no reply
