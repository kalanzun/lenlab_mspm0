import pytest

from lenlab.spy import Spy
from lenlab.terminal import Terminal, pack


@pytest.fixture
def terminal(port_infos) -> Terminal:
    terminal = Terminal()
    if not terminal.open(port_infos):
        pytest.skip("no port")

    yield terminal
    terminal.close()


def test_bsl_connect(terminal: Terminal):
    data_spy = Spy(terminal.data)
    with Spy(terminal.reply, 300) as spy:
        terminal.write(bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE)))

    if spy.count() == 1:
        reply = spy.get_single()
    elif data_spy.count() == 1:
        reply = data_spy.get_single()
    else:
        assert False

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


def test_knock(terminal: Terminal):
    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_hitchhiker(terminal: Terminal):
    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock") + b"knock")

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    with Spy(terminal.reply) as spy:
        pass

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_command_too_short(terminal: Terminal):
    with Spy(terminal.reply) as spy:
        terminal.write(b"Lk\x05\x00")

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_change_baudrate(terminal: Terminal):
    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    # with Spy(terminal.data) as spy:
    with Spy(terminal.port.bytesWritten) as tx:
        terminal.write(pack(b"b4MBd"))
    assert tx.get_single() == 8

    assert terminal.port.setBaudRate(4_000_000)
    assert terminal.port.clear()

    # reply = spy.get_single()
    # assert reply is None
    # assert reply == b"Lb\x00\x004MBd"

    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    # with Spy(terminal.data) as spy:
    with Spy(terminal.port.bytesWritten) as tx:
        terminal.write(pack(b"b9600"))
    assert tx.get_single() == 8

    assert terminal.port.setBaudRate(9_600)
    assert terminal.port.clear()

    # reply = spy.get_single()
    # assert reply is None
    # assert reply == b"Lb\x00\x004MBd"

    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"
