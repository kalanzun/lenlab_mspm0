import numpy as np
import pytest
from PySide6.QtSerialPort import QSerialPort

from importlib import resources

import lenlab
from lenlab.bsl import BootstrapLoader
from lenlab.terminal import Terminal
from lenlab.tests.spy import Spy
from lenlab.protocol import pack
from lenlab.terminal import Terminal
from lenlab.tests.memory import check_memory, memory_28k
from lenlab.tests.spy import Spy

from logging import getLogger
logger = getLogger(__name__)


@pytest.fixture(scope="module")
def terminal(port: QSerialPort) -> Terminal:
    terminal = Terminal(port)
    # port is already open
    yield terminal
    terminal.close()


def test_bsl_connect(bsl, terminal: Terminal):
    spy = Spy(terminal.ack)
    reply = Spy(terminal.reply)
    terminal.write(bsl.connect_packet)
    ack = spy.run_until_single_arg()
    assert ack == b"\x00"
    # an ok response might follow
    reply.run_until()


def knock(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(firmware.knock_packet)
    reply = spy.run_until_single_arg()
    assert reply == firmware.knock_packet[1:]


def test_knock(firmware, terminal: Terminal):
    knock(firmware, terminal)


def test_hitchhiker(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"knoc") + b"knock")
    reply = spy.run_until_single_arg()
    assert reply == pack(b"knoc")[1:]

    spy = Spy(terminal.reply)
    assert not spy.run_until()

    knock(firmware, terminal)


def test_command_too_short(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(b"Lk\x05\x00")
    assert not spy.run_until()

    knock(firmware, terminal)


@pytest.fixture(scope="module")
def memory(terminal: Terminal) -> np.ndarray:
    spy = Spy(terminal.reply)
    terminal.write(pack(b"mini"))  # memory init
    reply = spy.run_until_single_arg(timeout=600)
    assert reply == pack(b"mini")[1:]

    return memory_28k()


# @pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, terminal: Terminal, memory: np.ndarray):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"mget"))  # memory get
    reply = spy.run_until_single_arg(timeout=600)
    assert reply is not None, "no reply"
    check_memory(b"mget", memory, reply)


@pytest.fixture(scope="module")
def firmware_bin():
    return (resources.files(lenlab) / "lenlab_fw.bin").read_bytes()


def test_flash(flash, terminal: Terminal, firmware_bin: bytes):
    # assume cold BSL
    loader = BootstrapLoader(terminal)
    loader.message.connect(logger.info)
    terminal.error.connect(logger.warning)

    spy = Spy(loader.finished)
    loader.program(firmware_bin)
    assert spy.run_until_single_arg(1000)  # no success or timeout
