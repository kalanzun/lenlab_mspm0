import pytest

from lenlab.terminal import SyncTerminal, packet


@pytest.fixture
def terminal(port) -> SyncTerminal:
    return SyncTerminal(port)


def test_knock(firmware, terminal: SyncTerminal):
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_incomplete_packet(firmware, terminal: SyncTerminal):
    terminal.write(b"L\x05\x00")
    assert not terminal.wait_for_packet()

    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_wrong_baudrate(firmware, terminal: SyncTerminal):
    terminal.port.setBaudRate(4_000_000)
    terminal.write(packet(b"knock"))
    assert not terminal.wait_for_packet()

    terminal.port.setBaudRate(9_600)
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_hitchhiker(firmware, terminal: SyncTerminal):
    terminal.write(packet(b"knock") + b"knock")
    assert terminal.read_packet() == packet(b"hello")

    assert not terminal.wait_for_packet()
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_reply_too_long(firmware, terminal: SyncTerminal):
    terminal.write(packet(b"get10"))
    assert terminal.read_packet() == packet(b"get10")

    assert not terminal.wait_for_packet()
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")


def test_baudrate(firmware, terminal: SyncTerminal):
    terminal.write(packet(b"b4MBd"))
    terminal.wait_for_transmission()

    terminal.port.setBaudRate(4_000_000)
    assert terminal.read_packet(timeout=300) == packet(b"b4MBd")
    terminal.write(packet(b"knock"))
    assert terminal.read_packet() == packet(b"hello")

    terminal.write(packet(b"b9600"))
    terminal.wait_for_transmission()

    terminal.port.setBaudRate(9_600)
    assert terminal.read_packet(timeout=300) == packet(b"b9600")


def test_probe(firmware, terminal: SyncTerminal):
    terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert terminal.read_packet() == packet(b"hello")


def test_probe_bsl(bsl, terminal: SyncTerminal):
    terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert terminal.read_packet(length=10) == bytes.fromhex("00 08 02 00 3B 06 0D A7 F7 6B")
