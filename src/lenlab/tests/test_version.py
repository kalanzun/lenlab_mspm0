from importlib import metadata


def test_version():
    version = metadata.version("lenlab")
    assert len(version) >= 3
    assert len(version) <= 6
    assert version[1] == "."
