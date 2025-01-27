from lenlab.launchpad.protocol import command, pack


def test_pack():
    assert pack(b"knock") == b"Lk\x00\x00nock"


def test_command():
    assert command(b"knock", 1, 2, 3, 4) == b"Lk\x08\x00nock\x01\x00\x02\x00\x03\x00\x04\x00"
