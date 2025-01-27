from importlib import metadata


def pack(code: bytes, arg: bytes = b"\x00\x00\x00\x00", length: int = 0) -> bytes:
    assert len(code) == 1
    assert len(arg) == 4
    return b"L" + code + length.to_bytes(2, byteorder="little") + arg


def command(code: bytes, arg: int = 0, *payload: int) -> bytes:
    assert 0 <= len(payload) <= 4
    payload = list(payload) + [0] * (4 - len(payload))
    payload = b"".join(x.to_bytes(2, byteorder="little") for x in payload)
    return pack(code, arg.to_bytes(4, byteorder="little"), 8) + payload


def unpack_fw_version(reply: bytes) -> str | None:
    if reply[0:4] == b"L8\x00\x00":
        return "8." + reply[4:8].strip(b"\x00").decode("ascii", errors="strict")


def get_app_version() -> str:
    # compare without bugfix release (third version number)
    major, minor, *rest = metadata.version("lenlab").split(".")
    return f"{major}.{minor}"


def get_example_version_reply() -> bytes:
    version = get_app_version()
    return b"L8\x00\x00" + version[2:].encode("ascii").ljust(4, b"\x00")
