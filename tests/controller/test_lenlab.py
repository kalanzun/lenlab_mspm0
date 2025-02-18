import pytest

from lenlab.controller.lenlab import Lenlab, Lock
from lenlab.launchpad.terminal import ResourceError, Terminal
from lenlab.spy import Spy


def test_lock():
    lock = Lock()
    assert lock.is_locked

    spy = Spy(lock.locked)
    assert not lock.acquire()
    assert spy.count() == 0

    lock.release()
    assert spy.count() == 1
    assert not lock.is_locked

    assert lock.acquire()
    assert spy.count() == 2
    assert lock.is_locked


@pytest.fixture
def lenlab():
    return Lenlab()


def test_lenlab(lenlab):
    assert lenlab


def test_on_terminal_ready(lenlab):
    spy = Spy(lenlab.ready)
    lenlab.discovery.ready.emit(Terminal())
    assert spy.get_single_arg() is True
    assert lenlab.lock.is_locked is False


def test_on_terminal_error(lenlab):
    lenlab.discovery.ready.emit(terminal := Terminal())
    spy = Spy(lenlab.ready)
    terminal.error.emit(ResourceError())
    assert spy.get_single_arg() is False
    assert lenlab.lock.is_locked is True
