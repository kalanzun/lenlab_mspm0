import pytest

from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


class StaticReplyTerminal(Terminal):
    def __init__(self, packet: bytes):
        super().__init__("COM0")
        self.packet = packet

    @property
    def bytes_available(self) -> int:
        return len(self.packet)

    def peek(self, n: int) -> bytes:
        return self.packet[:n]

    def read(self, n: int) -> bytes:
        chunk, self.packet = self.packet[:n], self.packet[n:]
        return chunk

    def capture(self) -> tuple[Spy, Spy, Spy]:
        ack = Spy(self.ack)
        error = Spy(self.error)
        reply = Spy(self.reply)

        self.on_ready_read()

        count = ack.count() + error.count() + reply.count()
        assert count <= 1

        return ack, error, reply

    def capture_ack(self) -> int:
        self.ack_mode = True
        ack, error, reply = self.capture()
        # consume everything
        assert self.packet == b""
        return ack.count()

    def capture_reply(self) -> bytes | None:
        ack, error, reply = self.capture()
        # consume everything
        assert self.packet == b""
        return reply.get_single_arg()

    def capture_error(self) -> str | None:
        ack, error, reply = self.capture()
        # drop invalid bytes
        assert self.packet == b""
        return error.get_single_arg()

    def capture_nothing(self) -> bool:
        ack, error, reply = self.capture()
        count = ack.count() + error.count() + reply.count()
        return count == 0


knock = b"Lk\x00\x00nock"
ok = bytes((0x00, 0x08, 0x02, 0x00, 0x3B, 0x00, 0x38, 0x02, 0x94, 0x82))


def test_knock_packet():
    terminal = StaticReplyTerminal(knock)
    reply = terminal.capture_reply()
    assert reply == knock


def test_bsl_ok_packet():
    terminal = StaticReplyTerminal(ok)
    reply = terminal.capture_reply()
    assert reply == ok


def test_bsl_ack_success():
    terminal = StaticReplyTerminal(b"\x00")
    count = terminal.capture_ack()
    assert count == 1


@pytest.mark.parametrize("packet", [b"L", b"\x00", b"\x00\x08", knock[:4]])
def test_valid_prefix(packet):
    terminal = StaticReplyTerminal(packet)
    # do not consume a valid prefix
    assert terminal.capture_nothing()
    assert terminal.packet == packet


@pytest.mark.parametrize("packet", [b"Q", b"\x00\x80", b"QQQQ", b"\x00" + knock])
def test_invalid_prefix(packet):
    terminal = StaticReplyTerminal(packet)
    assert terminal.capture_error()


@pytest.mark.parametrize("packet", [knock + b"\x00", ok + bytes([0x51])])
def test_invalid_postfix(packet):
    terminal = StaticReplyTerminal(packet)
    assert terminal.capture_error()


@pytest.mark.parametrize(
    "packet", [b"L", knock, knock + b"\x00", b"Q", b"QQQQ", b"\x00\x08", b"\x00\x00"]
)
def test_invalid_bytes_ack_mode(packet):
    terminal = StaticReplyTerminal(packet)
    count = terminal.capture_ack()
    assert count == 0
    # drop invalid bytes
    assert terminal.packet == b""
