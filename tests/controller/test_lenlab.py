import pytest

from lenlab.controller.lenlab import Lenlab, Lock, NoReply
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


def test_on_reply(lenlab):
    lenlab.lock.release()
    lenlab.send_command(b"Lk\x08\x00nock, knock!")

    spy = Spy(lenlab.reply)
    lenlab.on_reply(b"Lk\x00\x00nock")

    assert spy.get_single_arg() == b"Lk\x00\x00nock"
    assert lenlab.lock.is_locked is False
    assert lenlab.timer.isActive() is False


def test_on_bsl_reply(lenlab):
    lenlab.discovery.ready.emit(terminal := Terminal())

    spy = Spy(lenlab.reply)
    terminal.reply.emit(b"\x00\x08")

    assert spy.count() == 0


def test_on_timeout(lenlab):
    spy = Spy(lenlab.error)
    lenlab.timer.timeout.emit()

    assert isinstance(spy.get_single_arg(), NoReply)


def test_send_command(lenlab):
    lenlab.lock.release()

    spy = Spy(lenlab.write)

    lenlab.send_command(b"Lk\x08\x00nock, knock!")
    assert spy.get_single_arg() == b"Lk\x08\x00nock, knock!"

    assert lenlab.lock.is_locked is True
    assert lenlab.timer.isActive() is True
