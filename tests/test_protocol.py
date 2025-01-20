from importlib import metadata

from lenlab.launchpad.protocol import get_app_version, pack, pack_uint32, unpack_fw_version


def test_pack():
    assert pack(b"8ver?") == b"L8\x00\x00ver?"


def test_pack_uint32():
    assert pack_uint32(b"l", 0xDEADBEEF) == b"Ll\x00\x00\xef\xbe\xad\xde"


def test_unpack_fw_version():
    assert unpack_fw_version(b"L8\x00\x002a1\x00") == "8.2a1"


def test_get_app_version(monkeypatch):
    monkeypatch.setattr(metadata, "version", lambda name: "8.2.1")
    assert get_app_version() == "8.2"
