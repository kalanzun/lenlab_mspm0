from importlib import metadata


def pack(argument: bytes, length: int = 0) -> bytes:
    assert len(argument) == 5
    return b"L" + argument[0:1] + length.to_bytes(2, byteorder="little") + argument[1:]


def pack_uint32(code: bytes, arg: int) -> bytes:
    assert len(code) == 1
    return b"L" + code + b"\x00\x00" + arg.to_bytes(4, byteorder="little")


def unpack_fw_version(reply: bytes) -> str | None:
    if reply[0:4] == b"L8\x00\x00":
        return "8." + reply[4:8].strip(b"\x00").decode("ascii", errors="strict")


def get_app_version() -> str:
    # compare without bugfix release (third version number)
    major, minor, *rest = metadata.version("lenlab").split(".")
    return f"{major}.{minor}"
