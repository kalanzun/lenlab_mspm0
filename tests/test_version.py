from importlib import metadata


def test_version():
    version = metadata.version("lenlab")
    assert len(version) >= 3
    assert len(version) <= 5
    assert version[1] == "."
