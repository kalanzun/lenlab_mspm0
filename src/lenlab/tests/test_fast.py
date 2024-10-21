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
    with Spy(terminal.reply) as spy:
        terminal.write(bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE)))

    reply = spy.get_single()
    # BSL does not reply to the fast terminal
    assert reply == b"Lk\x00\x00nock"


def test_fast_knock(terminal: Terminal):
    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_fast_hitchhiker(terminal: Terminal):
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


def test_fast_command_too_short(terminal: Terminal):
    with Spy(terminal.reply) as spy:
        terminal.write(b"Lk\x05\x00")

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.reply) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


# @pytest.mark.repeat(1000)
def test_fast_and_big(terminal: Terminal):
    # time-based packets 50ms: 3 errors in 1000 transmissions, 500s
    # length-based packets 100ms: 1000 transmissions in 120s
    # with the same terminal object (fixture scope module): 3 errors in 1000 transmissions 120s
    # with 250ms: no errors in 120s
    with Spy(terminal.reply, 300) as spy:
        terminal.write(pack(b"m30KB"))

    reply = spy.get_single()
    head = reply[0:4]
    assert head == b"Lm\x00\x78"
    payload = reply[4:8]
    assert payload == b"30KB"
    values = reply[8:]
    assert len(values) == 30 * 1024
