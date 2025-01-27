from importlib import metadata

from lenlab.launchpad import protocol


def test_pack():
    assert protocol.pack(b"k", b"nock") == b"Lk\x00\x00nock"


def test_command():
    packet = protocol.command(b"k", 0, 1, 2, 3, 4)
    assert packet == b"Lk\x08\x00\x00\x00\x00\x00\x01\x00\x02\x00\x03\x00\x04\x00"


def test_unpack_fw_version():
    assert protocol.unpack_fw_version(b"L8\x00\x002a1\x00") == "8.2a1"


def test_get_app_version(monkeypatch):
    monkeypatch.setattr(metadata, "version", lambda name: "8.2.1")
    assert protocol.get_app_version() == "8.2"


def test_get_example_version_reply(monkeypatch):
    monkeypatch.setattr(metadata, "version", lambda name: "8.2a1")
    assert protocol.get_example_version_reply() == b"L8\x00\x002a1\x00"
