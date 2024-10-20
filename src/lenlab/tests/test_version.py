from importlib import metadata


def test_version():
    assert metadata.version("lenlab")
