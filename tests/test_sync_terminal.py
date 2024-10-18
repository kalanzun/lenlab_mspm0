import pytest

from lenlab.terminal import SyncTerminal, packet


@pytest.fixture(scope="module")
def terminal() -> SyncTerminal:
    terminal = SyncTerminal()
    if terminal.open():
        assert terminal.probe()

    yield terminal

    terminal.close()


@pytest.fixture
def bsl(terminal: SyncTerminal) -> SyncTerminal:
    if not terminal.bsl:
        pytest.skip("bsl required")

    return terminal


@pytest.fixture
def firmware(terminal: SyncTerminal) -> SyncTerminal:
    if not terminal.firmware:
        pytest.skip("firmware required")

    return terminal


def test_knock(firmware: SyncTerminal):
    firmware.write(packet(b"knock"))
    assert firmware.read_packet() == packet(b"hello")


def test_incomplete_packet(firmware: SyncTerminal):
    firmware.write(b"L\x05\x00")
    assert not firmware.read_packet()

    firmware.write(packet(b"knock"))
    assert firmware.read_packet() == packet(b"hello")


def test_wrong_baudrate(firmware: SyncTerminal):
    firmware.port.setBaudRate(4_000_000)
    firmware.write(packet(b"knock"))
    assert not firmware.read_packet()

    firmware.port.setBaudRate(9_600)
    firmware.write(packet(b"knock"))
    assert firmware.read_packet() == packet(b"hello")


def test_hitchhiker(firmware: SyncTerminal):
    firmware.write(packet(b"knock") + b"knock")
    assert firmware.read_packet() == packet(b"hello")

    assert not firmware.read_packet()
    firmware.write(packet(b"knock"))
    assert firmware.read_packet() == packet(b"hello")


def test_reply_too_long(firmware: SyncTerminal):
    firmware.write(packet(b"get10"))
    assert firmware.read_packet() == packet(b"get10")

    assert not firmware.read_packet()
    firmware.write(packet(b"knock"))
    assert firmware.read_packet() == packet(b"hello")


def test_baudrate(firmware: SyncTerminal):
    firmware.write(packet(b"b4MBd"))
    firmware.wait_for_transmission()

    firmware.port.setBaudRate(4_000_000)
    assert firmware.read_packet(timeout=300) == packet(b"b4MBd")
    firmware.write(packet(b"knock"))
    assert firmware.read_packet() == packet(b"hello")

    firmware.write(packet(b"b9600"))
    firmware.wait_for_transmission()

    firmware.port.setBaudRate(9_600)
    assert firmware.read_packet(timeout=300) == packet(b"b9600")


def test_probe(firmware: SyncTerminal):
    firmware.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert firmware.read_packet() == packet(b"hello")


def test_probe_bsl(bsl: SyncTerminal):
    bsl.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert bsl.read_packet() == b"\x00"
    # probing already connected to the BSL. The BSL sends a core response on second connect.
    assert bsl.read_packet() == bytes.fromhex("08 02 00 3B 06 0D A7 F7 6B")
