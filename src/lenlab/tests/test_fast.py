import pytest

from lenlab.spy import Spy
from lenlab.terminal import Terminal, pack


@pytest.fixture
def terminal(port_infos) -> Terminal:
    terminal = Terminal()
    if not terminal.open(port_infos):
        pytest.skip("no port")

    with Spy(terminal.port.bytesWritten) as tx:
        terminal.write(pack(b"b4MBd"))
    assert tx.get_single() == 8

    assert terminal.port.setBaudRate(4_000_000)
    assert terminal.port.clear()

    yield terminal

    with Spy(terminal.port.bytesWritten) as tx:
        terminal.write(pack(b"b9600"))
    assert tx.get_single() == 8

    terminal.close()


def test_fast_bsl_connect(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE)))

    reply = spy.get_single()
    assert reply is not None
    assert len(reply) in {1, 8, 10}

    # firmware
    if len(reply) == 8:
        assert reply.startswith(b"Lk\x00\x00")

    # bsl
    elif len(reply) == 1:
        assert reply == b"\x00"
    elif len(reply) == 10:
        assert reply == bytes(
            (0x00, 0x08, 0x02, 0x00, 0x3B, 0x06, 0x0D, 0xA7, 0xF7, 0x6B)
        )


def test_fast_knock(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_fast_hitchhiker(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock") + b"knock")

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    with Spy(terminal.data) as spy:
        pass

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_fast_command_too_short(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(b"Lk\x05\x00")

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"
