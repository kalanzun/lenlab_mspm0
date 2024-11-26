from importlib import metadata

from lenlab.launchpad.protocol import get_app_version, pack, unpack_fw_version
from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


def test_version_specification():
    version = metadata.version("lenlab")
    assert len(version) >= 3
    assert len(version) <= 5
    assert version[1] == "."


def test_firmware_version(firmware, terminal: Terminal):
    spy = Spy(terminal.reply)
    terminal.write(pack(b"8ver?"))
    reply = spy.run_until_single_arg()

    fw_version = unpack_fw_version(reply)
    assert fw_version

    app_version = get_app_version()
    assert fw_version == app_version
