from importlib import metadata

from lenlab.launchpad.protocol import pack
from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


def test_version_specification():
    version = metadata.version("lenlab")
    assert len(version) >= 3
    assert len(version) <= 5
    assert version[1] == "."


def test_firmware_version(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(packet := pack(b"8ver?"))
    reply = spy.run_until_single_arg()
    assert reply[0:4] == packet[0:4]

    version = "8." + reply[4:8].strip(b"\x00").decode("ascii", errors="strict")
    assert version == metadata.version("lenlab")
